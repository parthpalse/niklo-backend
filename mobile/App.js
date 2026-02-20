import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet, Text, View, TextInput, TouchableOpacity,
  ScrollView, ActivityIndicator, Alert, SafeAreaView, KeyboardAvoidingView, Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from './config';

// ─── Storage keys ────────────────────────────────────────────────────────────
const KEY_PROFILE = 'niklo_profile';       // { home, station, walk_mins, arrival_time }
const KEY_DELAY_LOG = 'niklo_delay_log';     // { 0:[10,8,…], 1:[…], … }  (Mon=0 … Sun=6)
const MAX_DELAY_ENTRIES = 4;                  // keep last 4 per day

// ─── Helpers ─────────────────────────────────────────────────────────────────
const TIMEOUT_MS = 60_000;

async function postJSON(url, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

function avgDelay(log, day) {
  const entries = (log[day] || []);
  if (!entries.length) return 0;
  const sum = entries.reduce((a, b) => a + b, 0);
  return Math.round(sum / entries.length);
}

function dayOfWeekMon0() {
  // JS Sunday=0 → convert to Mon=0 … Sun=6
  const d = new Date().getDay();
  return d === 0 ? 6 : d - 1;
}

// ─── Screens ─────────────────────────────────────────────────────────────────

/** First-launch setup — collects home address, nearest station, walk time, arrival time. */
function SetupScreen({ onSave }) {
  const [home, setHome] = useState('');
  const [station, setStation] = useState('Thane');
  const [walkMins, setWalkMins] = useState('5');
  const [arrival, setArrival] = useState('09:00');
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!home.trim() || !station.trim() || !arrival.trim()) {
      Alert.alert('Missing', 'Please fill in all fields.');
      return;
    }
    if (!/^\d{2}:\d{2}$/.test(arrival)) {
      Alert.alert('Format', 'Arrival time must be HH:MM (e.g. 09:00).');
      return;
    }
    setSaving(true);
    const profile = { home: home.trim(), station: station.trim(), walk_mins: parseInt(walkMins) || 5, arrival_time: arrival.trim() };
    await AsyncStorage.setItem(KEY_PROFILE, JSON.stringify(profile));
    onSave(profile);
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.setupScroll}>
        <Text style={styles.header}>ClgBuddy 🚆</Text>
        <Text style={styles.subHeader}>Set up once — we remember forever</Text>

        <View style={styles.card}>
          <Text style={styles.label}>🏠 Home Address</Text>
          <TextInput style={styles.input} value={home} onChangeText={setHome}
            placeholder="e.g. Thane West, near Upvan Lake" />

          <Text style={styles.label}>🚉 Nearest Railway Station</Text>
          <TextInput style={styles.input} value={station} onChangeText={setStation}
            placeholder="e.g. Thane" />

          <Text style={styles.label}>🚶 Walk time: Station → KJSCE gate (mins)</Text>
          <TextInput style={styles.input} value={walkMins} onChangeText={setWalkMins}
            placeholder="5" keyboardType="number-pad" />

          <Text style={styles.label}>🎯 Desired arrival time at KJSCE (HH:MM)</Text>
          <TextInput style={styles.input} value={arrival} onChangeText={setArrival}
            placeholder="09:00" keyboardType="number-pad" />

          <TouchableOpacity style={styles.button} onPress={save} disabled={saving}>
            {saving
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.buttonText}>Save & Continue →</Text>}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

/** Main commute screen — calculates and shows the best route. */
function MainScreen({ profile, onReset }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [delayLog, setDelayLog] = useState({});
  const [logDelay, setLogDelay] = useState('');   // text input for logging actual delay
  const [logging, setLogging] = useState(false);

  const day = dayOfWeekMon0();

  // Load delay log on mount
  useEffect(() => {
    AsyncStorage.getItem(KEY_DELAY_LOG).then(raw => {
      if (raw) setDelayLog(JSON.parse(raw));
    });
  }, []);

  const predictedDelay = avgDelay(delayLog, day);

  const calculate = useCallback(async () => {
    setLoading(true);
    setResult(null);
    try {
      // Fire both requests in parallel using Promise.all
      const [plan, predictionReq] = await Promise.all([
        postJSON(`${API_URL}/api/commute`, {
          origin: profile.home,
          arrival_time: profile.arrival_time,
          delay_buffer_mins: predictedDelay,
        }),
        postJSON(`${API_URL}/api/predict`, {
          time: profile.arrival_time,
          day_of_week: day,
        }).catch(err => null)
      ]);

      const prediction = predictionReq ? predictionReq.predicted_duration_mins : null;
      setResult({ ...plan, prediction });
    } catch (err) {
      if (err.name === 'AbortError') {
        Alert.alert('Timed Out', 'Server took > 60 s. Try again later.');
      } else {
        Alert.alert('Error', 'Could not fetch commute plan. Is the backend running?');
      }
    } finally {
      setLoading(false);
    }
  }, [profile, predictedDelay, day]);

  const saveDelay = async () => {
    const mins = parseInt(logDelay);
    if (isNaN(mins) || mins < 0 || mins > 120) {
      Alert.alert('Invalid', 'Enter a delay in minutes (0–120).');
      return;
    }
    setLogging(true);
    const updated = { ...delayLog };
    const existing = updated[day] || [];
    updated[day] = [...existing, mins].slice(-MAX_DELAY_ENTRIES); // keep last 4
    await AsyncStorage.setItem(KEY_DELAY_LOG, JSON.stringify(updated));
    setDelayLog(updated);
    setLogDelay('');
    setLogging(false);
    Alert.alert('Saved!', `Logged ${mins} min delay for today. New average: ${avgDelay(updated, day)} mins.`);
  };

  const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <ScrollView contentContainerStyle={styles.mainScroll}>
      {/* Header */}
      <Text style={styles.header}>NikLo 🚆</Text>
      <Text style={styles.subHeader}>Home → KJSCE Vidyavihar</Text>

      {/* Profile summary */}
      <View style={styles.profileBar}>
        <Text style={styles.profileText}>🏠 {profile.home}</Text>
        <Text style={styles.profileText}>🚉 {profile.station} · ⏰ Arrive {profile.arrival_time}</Text>
        <TouchableOpacity onPress={onReset}>
          <Text style={styles.editLink}>Edit profile</Text>
        </TouchableOpacity>
      </View>

      {/* Delay badge */}
      <View style={[styles.delayBadge, predictedDelay > 0 ? styles.delayBadgeActive : {}]}>
        <Text style={styles.delayText}>
          {predictedDelay > 0
            ? `⚠️ ${DAY_NAMES[day]} usually runs ${predictedDelay} min late — buffer added`
            : `✅ No usual delay recorded for ${DAY_NAMES[day]}s`}
        </Text>
      </View>

      {/* Calculate button */}
      <TouchableOpacity style={styles.button} onPress={calculate} disabled={loading}>
        {loading
          ? <ActivityIndicator color="#fff" />
          : <Text style={styles.buttonText}>Calculate My Commute</Text>}
      </TouchableOpacity>

      {/* Results */}
      {result && (
        <View style={{ marginTop: 24 }}>
          {result.prediction != null && (
            <View style={styles.mlBadge}>
              <Text style={styles.mlText}>🔮 ML estimate: ~{Math.round(result.prediction)} mins total</Text>
            </View>
          )}

          <Text style={styles.recommendText}>
            Recommended: {result.recommendation === 'Train' ? '🚆 Train' : '🚗 Road'}
          </Text>

          {/* Train route card — only render if train_route !== null */}
          {result.train_route !== null ? (
            <View style={[styles.routeCard, result.recommendation === 'Train' && styles.winnerCard]}>
              <Text style={styles.cardTitle}>🚆 Train Route</Text>
              <Text style={styles.leaveAt}>Leave by {result.train_route.leave_at}</Text>
              <Text style={styles.info}>{result.train_route.details.leg1_road}</Text>
              <Text style={styles.info}>{result.train_route.details.leg2_train}</Text>
              <Text style={styles.info}>{result.train_route.details.leg3_walk}</Text>
              <Text style={styles.duration}>Total: {result.train_route.total_duration_mins} mins</Text>
            </View>
          ) : (
            <View style={styles.routeCard}>
              <Text style={styles.cardTitle}>🚆 Train Route</Text>
              <Text style={styles.info}>No feasible train found for this timing.</Text>
            </View>
          )}

          {/* Road route card */}
          <View style={[styles.routeCard, result.recommendation === 'Road' && styles.winnerCard]}>
            <Text style={styles.cardTitle}>🚗 Road Route</Text>
            <Text style={styles.leaveAt}>Leave by {result.road_route.leave_at}</Text>
            <Text style={styles.info}>{result.road_route.details.summary}</Text>
            <Text style={styles.duration}>Total: {result.road_route.total_duration_mins} mins</Text>
          </View>
        </View>
      )}

      {/* Log actual delay */}
      <View style={styles.logBox}>
        <Text style={styles.label}>📝 Log today's train delay (mins)</Text>
        <View style={styles.logRow}>
          <TextInput
            style={[styles.input, { flex: 1, marginBottom: 0 }]}
            value={logDelay}
            onChangeText={setLogDelay}
            placeholder="e.g. 8"
            keyboardType="number-pad"
          />
          <TouchableOpacity style={styles.logButton} onPress={saveDelay} disabled={logging}>
            {logging
              ? <ActivityIndicator color="#fff" size="small" />
              : <Text style={styles.logButtonText}>Save</Text>}
          </TouchableOpacity>
        </View>
        {(delayLog[day] || []).length > 0 && (
          <Text style={styles.delayHistory}>
            Last {(delayLog[day] || []).length} {DAY_NAMES[day]} delays: {(delayLog[day] || []).join(', ')} mins
          </Text>
        )}
      </View>
    </ScrollView>
  );
}

// ─── Root ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [profile, setProfile] = useState(null);   // null = not loaded yet
  const [ready, setReady] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(KEY_PROFILE).then(raw => {
      if (raw) setProfile(JSON.parse(raw));
      setReady(true);
    });
  }, []);

  const resetProfile = async () => {
    await AsyncStorage.removeItem(KEY_PROFILE);
    setProfile(null);
  };

  if (!ready) {
    return (
      <SafeAreaView style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color="#007AFF" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {profile
        ? <MainScreen profile={profile} onReset={resetProfile} />
        : <SetupScreen onSave={setProfile} />}
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0F4F8' },
  setupScroll: { padding: 24, paddingBottom: 48 },
  mainScroll: { padding: 20, paddingBottom: 48 },

  header: { fontSize: 34, fontWeight: '800', color: '#1A1A2E', textAlign: 'center', marginTop: 16 },
  subHeader: { fontSize: 15, color: '#666', textAlign: 'center', marginBottom: 24 },

  card: {
    backgroundColor: '#fff', borderRadius: 16, padding: 20,
    shadowColor: '#000', shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08, shadowRadius: 8, elevation: 4,
  },

  profileBar: {
    backgroundColor: '#fff', borderRadius: 12, padding: 14, marginBottom: 12,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06, shadowRadius: 4, elevation: 2,
  },
  profileText: { fontSize: 13, color: '#444', marginBottom: 3 },
  editLink: { fontSize: 13, color: '#007AFF', marginTop: 6 },

  delayBadge: { borderRadius: 10, padding: 10, backgroundColor: '#E8F5E9', marginBottom: 14 },
  delayBadgeActive: { backgroundColor: '#FFF3E0' },
  delayText: { fontSize: 13, color: '#333', textAlign: 'center' },

  label: { fontSize: 14, fontWeight: '600', color: '#444', marginBottom: 6, marginTop: 14 },
  input: {
    borderWidth: 1, borderColor: '#DDE3EA', borderRadius: 10,
    padding: 12, fontSize: 15, backgroundColor: '#FAFAFA', marginBottom: 4,
  },

  button: {
    backgroundColor: '#007AFF', padding: 16, borderRadius: 12,
    marginTop: 20, alignItems: 'center',
    shadowColor: '#007AFF', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3, shadowRadius: 8, elevation: 5,
  },
  buttonText: { color: '#fff', fontSize: 17, fontWeight: '700' },

  recommendText: {
    fontSize: 20, fontWeight: '700', color: '#1A1A2E',
    textAlign: 'center', marginBottom: 14,
  },

  routeCard: {
    backgroundColor: '#fff', borderRadius: 14, padding: 16,
    marginBottom: 14, borderWidth: 1.5, borderColor: '#E8ECF0',
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06, shadowRadius: 5, elevation: 2,
  },
  winnerCard: { borderColor: '#34C759', backgroundColor: '#F1FFF4' },
  cardTitle: { fontSize: 17, fontWeight: '700', color: '#1A1A2E', marginBottom: 10 },
  leaveAt: { fontSize: 22, fontWeight: '800', color: '#007AFF', marginBottom: 8 },
  info: { fontSize: 14, color: '#555', marginVertical: 3 },
  duration: { fontSize: 14, fontWeight: '600', color: '#333', marginTop: 8 },

  mlBadge: {
    backgroundColor: '#EEF2FF', borderRadius: 10, padding: 10,
    marginBottom: 14, borderWidth: 1, borderColor: '#C7D2FE', alignItems: 'center',
  },
  mlText: { color: '#4338CA', fontWeight: '600', fontSize: 13 },

  logBox: {
    marginTop: 28, backgroundColor: '#fff', borderRadius: 14, padding: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06, shadowRadius: 5, elevation: 2,
  },
  logRow: { flexDirection: 'row', gap: 10, alignItems: 'center' },
  logButton: { backgroundColor: '#34C759', borderRadius: 10, paddingHorizontal: 18, paddingVertical: 13 },
  logButtonText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  delayHistory: { fontSize: 12, color: '#888', marginTop: 8, textAlign: 'center' },
});
