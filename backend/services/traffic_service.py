import googlemaps
from datetime import datetime
from config import Config

class TrafficService:
    def __init__(self):
        self._gmaps = None

    @property
    def gmaps(self):
        if self._gmaps is None:
            if not Config.GOOGLE_MAPS_API_KEY:
                raise ValueError("GOOGLE_MAPS_API_KEY is not set")
            self._gmaps = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
        return self._gmaps


    def get_travel_time(self, origin, destination, mode='driving', departure_time=None):
        """
        Fetches travel time from Google Maps Distance Matrix API.
        :param origin: Starting location (string or tuple)
        :param destination: Destination location (string or tuple)
        :param mode: Mode of transport (driving, walking, bicycling, transit)
        :param departure_time: datetime object (defaults to now)
        :return: duration in seconds
        """
        if not departure_time:
            departure_time = datetime.now()

        try:
            result = self.gmaps.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode=mode,
                departure_time=departure_time
            )

            # Parse the result
            if result['status'] == 'OK':
                element = result['rows'][0]['elements'][0]
                if element['status'] == 'OK':
                    # duration_in_traffic is preferred if available (requires valid departure_time)
                    duration = element.get('duration_in_traffic', element.get('duration'))
                    return {
                        'duration_seconds': duration['value'],
                        'duration_text': duration['text'],
                        'distance_text': element['distance']['text']
                    }
                else:
                    return {'error': f"Element status: {element['status']}"}
            else:
                return {'error': f"API Error: {result['status']}"}

        except Exception as e:
            return {'error': str(e)}
