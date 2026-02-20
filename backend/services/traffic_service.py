import requests
from config import Config

ORS_BASE = 'https://api.openrouteservice.org'

# ---------------------------------------------------------------------------
# Pre-geocoded coordinates for every Mumbai Central Line station.
# Format: [longitude, latitude]  (ORS uses lng,lat order)
# These are fixed — no geocoding API call needed for these known points.
# ---------------------------------------------------------------------------
STATION_COORDS = {
    'CSMT':        [72.8347, 18.9399],
    'Masjid':      [72.8375, 18.9466],
    'Sandhurst Road': [72.8396, 18.9528],
    'Byculla':     [72.8394, 18.9757],
    'Chinchpokli': [72.8413, 18.9838],
    'Currey Road': [72.8413, 18.9919],
    'Parel':       [72.8434, 19.0000],
    'Dadar':       [72.8427, 19.0176],
    'Matunga':     [72.8560, 19.0273],
    'Sion':        [72.8601, 19.0393],
    'Kurla':       [72.8796, 19.0654],
    'Vidyavihar':  [72.9046, 19.0740],   # ← destination station for KJSCE
    'Ghatkopar':   [72.9088, 19.0861],
    'Vikhroli':    [72.9247, 19.1047],
    'Kanjurmarg':  [72.9418, 19.1122],
    'Bhandup':     [72.9523, 19.1228],
    'Nahur':       [72.9590, 19.1332],
    'Mulund':      [72.9668, 19.1716],
    'Thane':       [72.9615, 19.1820],
    'Kalwa':       [73.0030, 19.2005],
    'Mumbra':      [73.0218, 19.1840],
    'Diva':        [73.0600, 19.1780],
    'Kopar':       [73.0676, 19.1660],
    'Dombivli':    [73.0875, 19.2144],
    'Thakurli':    [73.0983, 19.2185],
    'Kalyan':      [73.1291, 19.2437],
    # Harbour / Transharbour stubs (for future use)
    'Vashi':       [72.9987, 19.0799],
    'Airoli':      [72.9999, 19.1548],
}

# Walking time in minutes from Vidyavihar station to KJSCE main gate.
# Measured once — hardcoded forever. No API call needed.
VIDYAVIHAR_TO_KJSCE_WALK_MINS = 7


class TrafficService:
    def __init__(self):
        pass

    def _get_key(self):
        if not Config.ORS_API_KEY:
            raise ValueError("ORS_API_KEY is not set in environment variables")
        return Config.ORS_API_KEY

    def _resolve_coords(self, address: str):
        """
        Return [lng, lat] for an address.
        If the address matches a known station name, return hardcoded coords
        instantly (no API call). Otherwise geocode via ORS.
        """
        # Check against known stations (case-insensitive, partial match)
        addr_lower = address.lower().replace(' railway station', '').replace(' station', '').strip()
        for station, coords in STATION_COORDS.items():
            if station.lower() == addr_lower:
                return coords

        # Fallback: geocode via ORS (only for home addresses)
        url = f"{ORS_BASE}/geocode/search"
        params = {
            'api_key': self._get_key(),
            'text': address,
            # Bias results towards Mumbai/Thane bounding box
            'boundary.rect.min_lon': 72.75,
            'boundary.rect.min_lat': 18.85,
            'boundary.rect.max_lon': 73.25,
            'boundary.rect.max_lat': 19.40,
            'size': 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        features = resp.json().get('features', [])
        if not features:
            raise ValueError(f"Could not geocode address: {address}")
        return features[0]['geometry']['coordinates']

    def get_travel_time(self, origin: str, destination: str):
        """
        Returns road travel time between origin and destination.
        Uses hardcoded coords for known stations; geocodes only home addresses.
        """
        try:
            origin_coords = self._resolve_coords(origin)
            dest_coords   = self._resolve_coords(destination)

            url = f"{ORS_BASE}/v2/matrix/driving-car"
            headers = {
                'Authorization': self._get_key(),
                'Content-Type': 'application/json',
            }
            body = {
                "locations": [origin_coords, dest_coords],
                "metrics":   ["duration", "distance"],
                "units":     "km",
            }

            resp = requests.post(url, json=body, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            duration_seconds = data['durations'][0][1]
            distance_km      = data['distances'][0][1]

            duration_mins = int(duration_seconds / 60)
            duration_text = (
                f"{duration_mins} mins" if duration_mins < 60
                else f"{duration_mins // 60}h {duration_mins % 60}m"
            )

            return {
                'duration_seconds': int(duration_seconds),
                'duration_text':    duration_text,
                'distance_text':    f"{round(distance_km, 1)} km",
            }

        except ValueError as e:
            return {'error': str(e)}
        except requests.exceptions.HTTPError as e:
            return {'error': f"ORS API error: {e.response.status_code} - {e.response.text[:200]}"}
        except Exception as e:
            return {'error': str(e)}
