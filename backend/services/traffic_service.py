import requests
from config import Config

# ORS API base URL
ORS_BASE = 'https://api.openrouteservice.org'

class TrafficService:
    def __init__(self):
        self.api_key = None  # Lazy init

    def _get_key(self):
        if not Config.ORS_API_KEY:
            raise ValueError("ORS_API_KEY is not set in environment variables")
        return Config.ORS_API_KEY

    def _geocode(self, address):
        """Convert address string to [longitude, latitude] using ORS Geocoding."""
        url = f"{ORS_BASE}/geocode/search"
        params = {
            'api_key': self._get_key(),
            'text': address,
            'size': 1
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        features = resp.json().get('features', [])
        if not features:
            raise ValueError(f"Could not geocode address: {address}")
        coords = features[0]['geometry']['coordinates']  # [lng, lat]
        return coords

    def get_travel_time(self, origin, destination, mode='driving', departure_time=None):
        """
        Gets travel time using ORS Matrix API.
        Returns duration in seconds and distance in km.
        """
        try:
            origin_coords = self._geocode(origin)
            dest_coords = self._geocode(destination)

            url = f"{ORS_BASE}/v2/matrix/driving-car"
            headers = {
                'Authorization': self._get_key(),
                'Content-Type': 'application/json'
            }
            body = {
                "locations": [origin_coords, dest_coords],
                "metrics": ["duration", "distance"],
                "units": "km"
            }

            resp = requests.post(url, json=body, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            duration_seconds = data['durations'][0][1]
            distance_km = data['distances'][0][1]

            # Format nicely
            duration_mins = int(duration_seconds / 60)
            duration_text = f"{duration_mins} mins" if duration_mins < 60 else f"{duration_mins // 60}h {duration_mins % 60}m"
            distance_text = f"{round(distance_km, 1)} km"

            return {
                'duration_seconds': int(duration_seconds),
                'duration_text': duration_text,
                'distance_text': distance_text
            }

        except ValueError as e:
            return {'error': str(e)}
        except requests.exceptions.HTTPError as e:
            return {'error': f"ORS API error: {e.response.status_code} - {e.response.text[:200]}"}
        except Exception as e:
            return {'error': str(e)}
