import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, Alert, SafeAreaView } from 'react-native';
import { API_URL } from './config';

export default function App() {
  const [origin, setOrigin] = useState('Thane West');
  const [destination, setDestination] = useState('CSMT');
  const [arrivalTime, setArrivalTime] = useState('09:00');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const postJSON = async (url, body) => {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  };

  const fetchCommutePlan = async () => {
    if (!origin || !destination || !arrivalTime) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    setLoading(true);
    setResult(null);

    const dayOfWeek = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1;

    try {
      const plan = await postJSON(`${API_URL}/api/commute`, {
        origin,
        destination,
        arrival_time: arrivalTime,
      });

      let prediction = null;
      try {
        const mlRes = await postJSON(`${API_URL}/api/predict`, {
          time: arrivalTime,
          day_of_week: dayOfWeek,
        });
        prediction = mlRes.predicted_duration_mins;
      } catch (e) {
        console.log('ML Prediction failed:', e.message);
      }

      setResult({ ...plan, prediction });
    } catch (error) {
      Alert.alert('Error', 'Failed to fetch commute plan. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.header}>NikLo</Text>
        <Text style={styles.subHeader}>Smart Commute Assistant</Text>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>Origin</Text>
          <TextInput
            style={styles.input}
            value={origin}
            onChangeText={setOrigin}
            placeholder="e.g. Thane West"
          />
          <Text style={styles.label}>Destination</Text>
          <TextInput
            style={styles.input}
            value={destination}
            onChangeText={setDestination}
            placeholder="e.g. CSMT"
          />
          <Text style={styles.label}>Arrival Time (HH:MM)</Text>
          <TextInput
            style={styles.input}
            value={arrivalTime}
            onChangeText={setArrivalTime}
            placeholder="09:00"
            keyboardType="number-pad"
          />
          <TouchableOpacity style={styles.button} onPress={fetchCommutePlan} disabled={loading}>
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Find Best Route</Text>
            )}
          </TouchableOpacity>
        </View>

        {result && (
          <View style={styles.resultContainer}>
            {result.prediction != null && (
              <View style={styles.mlBadge}>
                <Text style={styles.mlText}>🔮 ML Prediction: ~{Math.round(result.prediction)} mins</Text>
              </View>
            )}

            <Text style={styles.resultHeader}>Recommended: {result.recommendation}</Text>

            <View style={[styles.card, result.recommendation === 'Train' ? styles.recommendedCard : {}]}>
              <Text style={styles.cardTitle}>🚆 Train Route</Text>
              {result.train_route ? (
                <>
                  <Text style={styles.info}>Leave at: <Text style={styles.bold}>{result.train_route.leave_at}</Text></Text>
                  <Text style={styles.info}>Total: {result.train_route.total_duration_mins} mins</Text>
                  <View style={styles.details}>
                    <Text style={styles.detailText}>1. {result.train_route.details.leg1_road}</Text>
                    <Text style={styles.detailText}>2. {result.train_route.details.leg2_train}</Text>
                    <Text style={styles.detailText}>3. {result.train_route.details.leg3_road}</Text>
                  </View>
                </>
              ) : (
                <Text style={styles.info}>No feasible train route found.</Text>
              )}
            </View>

            <View style={[styles.card, result.recommendation === 'Road' ? styles.recommendedCard : {}]}>
              <Text style={styles.cardTitle}>🚗 Road Route</Text>
              <Text style={styles.info}>Leave at: <Text style={styles.bold}>{result.road_route.leave_at}</Text></Text>
              <Text style={styles.info}>Total: {result.road_route.total_duration_mins} mins</Text>
              <Text style={styles.detailText}>{result.road_route.details.summary}</Text>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  scrollContent: { padding: 20 },
  header: { fontSize: 32, fontWeight: 'bold', color: '#333', textAlign: 'center', marginTop: 20 },
  subHeader: { fontSize: 16, color: '#666', textAlign: 'center', marginBottom: 30 },
  inputContainer: {
    backgroundColor: '#fff', padding: 20, borderRadius: 15,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1, shadowRadius: 5, elevation: 3,
  },
  label: { fontSize: 14, fontWeight: '600', color: '#444', marginBottom: 5, marginTop: 10 },
  input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12, fontSize: 16, backgroundColor: '#fafafa' },
  button: { backgroundColor: '#007AFF', padding: 15, borderRadius: 10, marginTop: 20, alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  resultContainer: { marginTop: 30 },
  resultHeader: { fontSize: 22, fontWeight: 'bold', marginBottom: 15, textAlign: 'center', color: '#333' },
  card: { backgroundColor: '#fff', padding: 15, borderRadius: 12, marginBottom: 15, borderWidth: 1, borderColor: '#eee' },
  recommendedCard: { borderColor: '#4CAF50', borderWidth: 2, backgroundColor: '#F1F8E9' },
  cardTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 10, color: '#222' },
  info: { fontSize: 16, marginBottom: 5, color: '#444' },
  bold: { fontWeight: 'bold' },
  details: { marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#eee' },
  detailText: { fontSize: 14, color: '#666', marginVertical: 2 },
  mlBadge: { backgroundColor: '#E1F5FE', padding: 10, borderRadius: 8, marginBottom: 15, alignItems: 'center', borderWidth: 1, borderColor: '#0288D1' },
  mlText: { color: '#0277BD', fontWeight: 'bold' },
});
