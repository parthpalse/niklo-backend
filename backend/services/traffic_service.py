import requests
from config import Config

# ---------------------------------------------------------------------------
# Free, keyless APIs — no API key required, always available
#   Geocoding : Nominatim (OpenStreetMap) — nominatim.openstreetmap.org
#   Routing   : OSRM demo server         — router.project-osrm.org
# ---------------------------------------------------------------------------

NOMINATIM_BASE = 'https://nominatim.openstreetmap.org'
OSRM_BASE      = 'https://router.project-osrm.org'

# Required by Nominatim TOS: identify your app in User-Agent
HEADERS = {'User-Agent': 'ClgBuddy-App/1.0 (student commute assistant)'}

# ---------------------------------------------------------------------------
# Pre-geocoded coordinates for every Mumbai Central Line station.
# Format : [longitude, latitude]   (OSRM uses lng,lat order)
# Having these hardcoded means ZERO API calls for station-to-station legs.
# ---------------------------------------------------------------------------
STATION_COORDS = {
    'CSMT':           [72.8347, 18.9399],
    'Masjid':         [72.8375, 18.9466],
    'Sandhurst Road': [72.8396, 18.9528],
    'Byculla':        [72.8394, 18.9757],
    'Chinchpokli':    [72.8413, 18.9838],
    'Currey Road':    [72.8413, 18.9919],
    'Parel':          [72.8434, 19.0000],
    'Dadar':          [72.8427, 19.0176],
    'Matunga':        [72.8560, 19.0273],
    'Sion':           [72.8601, 19.0393],
    'Kurla':          [72.8796, 19.0654],
    'Vidyavihar':     [72.9046, 19.0740],   # ← destination station for KJSCE
    'Ghatkopar':      [72.9088, 19.0861],
    'Vikhroli':       [72.9247, 19.1047],
    'Kanjurmarg':     [72.9418, 19.1122],
    'Bhandup':        [72.9523, 19.1228],
    'Nahur':          [72.9590, 19.1332],
    'Mulund':         [72.9668, 19.1716],
    'Thane':          [72.9615, 19.1820],
    'Kalwa':          [73.0030, 19.2005],
    'Mumbra':         [73.0218, 19.1840],
    'Diva':           [73.0600, 19.1780],
    'Kopar':          [73.0676, 19.1660],
    'Dombivli':       [73.0875, 19.2144],
    'Thakurli':       [73.0983, 19.2185],
    'Kalyan':         [73.1291, 19.2437],
    'Vashi':          [72.9987, 19.0799],
    'Turbhe':         [73.0163, 19.0782],
    'Koparkhairane':  [73.0016, 19.1030],
    'Ghansoli':       [72.9991, 19.1245],
    'Rabale':         [72.9994, 19.1368],
    'Airoli':         [72.9999, 19.1548],
    # KJSCE destination — hardcoded so Nominatim is never called for it
    'KJSCE':                              [72.9041, 19.0712],
    'K.J. Somaiya':                       [72.9041, 19.0712],
    'KJ Somaiya':                         [72.9041, 19.0712],
    'Somaiya':                            [72.9041, 19.0712],
    'KJSCE, Vidyavihar West, Mumbai, Maharashtra': [72.9041, 19.0712],
}

# Fixed walk time: Vidyavihar station exit → KJSCE main gate (measured once)
VIDYAVIHAR_TO_KJSCE_WALK_MINS = 7


class TrafficService:
    def __init__(self):
        pass  # no keys to initialise

    # ------------------------------------------------------------------
    def _resolve_coords(self, address: str):
        """
        Return [lng, lat] for an address.
        Checks hardcoded station dict first (instant, no HTTP).
        Falls back to Nominatim geocoding (free, no key).
        """
        addr_clean = (
            address.lower()
                   .replace(' railway station', '')
                   .replace(' station', '')
                   .strip()
        )
        for station, coords in STATION_COORDS.items():
            if station.lower() == addr_clean:
                return coords

        # Nominatim geocoding — biased to India (countrycodes=in)
        url = f"{NOMINATIM_BASE}/search"
        params = {
            'q':            address,
            'format':       'json',
            'limit':        1,
            'countrycodes': 'in',
            # Bias to Mumbai / Thane area via viewbox
            'viewbox':      '72.75,18.85,73.25,19.40',
            'bounded':      1,
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            # Retry without viewbox restriction (for edge-case addresses)
            params.pop('viewbox')
            params.pop('bounded')
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            results = resp.json()
        if not results:
            raise ValueError(f"Could not geocode address: {address}")
        lon = float(results[0]['lon'])
        lat = float(results[0]['lat'])
        return [lon, lat]

    # ------------------------------------------------------------------
    def get_travel_time(self, origin: str, destination: str):
        """
        Returns road travel time via OSRM demo server (no API key needed).
        """
        try:
            o_coords = self._resolve_coords(origin)
            d_coords = self._resolve_coords(destination)

            # OSRM route endpoint: /route/v1/driving/{lng1,lat1};{lng2,lat2}
            coords_str = f"{o_coords[0]},{o_coords[1]};{d_coords[0]},{d_coords[1]}"
            url = f"{OSRM_BASE}/route/v1/driving/{coords_str}"
            params = {'overview': 'false', 'steps': 'false'}

            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get('code') != 'Ok' or not data.get('routes'):
                return {'error': 'OSRM returned no route'}

            route           = data['routes'][0]
            duration_secs   = route['duration']   # seconds
            distance_m      = route['distance']   # metres
            duration_mins   = int(duration_secs / 60)
            distance_km     = round(distance_m / 1000, 1)

            duration_text = (
                f"{duration_mins} mins" if duration_mins < 60
                else f"{duration_mins // 60}h {duration_mins % 60}m"
            )

            return {
                'duration_seconds': int(duration_secs),
                'duration_text':    duration_text,
                'distance_text':    f"{distance_km} km",
            }

        except ValueError as e:
            return {'error': str(e)}
        except requests.exceptions.RequestException as e:
            return {'error': f"Routing error: {str(e)}"}
        except Exception as e:
            return {'error': str(e)}
