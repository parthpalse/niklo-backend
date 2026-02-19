from services.traffic_service import TrafficService
from services.train_service import TrainService
from datetime import datetime, timedelta
import heapq

class CommuteService:
    def __init__(self):
        self.traffic_service = TrafficService()
        self.train_service = TrainService()
        # Mapping common locations to nearest railway stations
        self.station_map = {
            'Thane West': 'Thane',
            'Thane East': 'Thane',
            'Mulund': 'Thane', # Approximation
            'Airoli': 'Thane', # Approximation
            'CSMT': 'CSMT',
            'Fort': 'CSMT',
            'Dadar': 'Dadar'
        }

    def calculate_best_route(self, origin, destination, arrival_time_str):
        """
        Calculates the best route (Road vs Train + Road combination).
        Uses a simplified shortest path approach.
        """
        
        # 1. Direct Road Route
        road_trip = self.traffic_service.get_travel_time(origin, destination)
        
        if 'error' in road_trip:
            return {'error': 'Could not fetch traffic data'}

        road_duration_mins = road_trip['duration_seconds'] / 60
        arrival_dt = datetime.strptime(arrival_time_str, '%H:%M') 
        # For today
        arrival_dt = datetime.combine(datetime.now().date(), arrival_dt.time())
        
        road_departure_dt = arrival_dt - timedelta(minutes=road_duration_mins)
        
        # 2. Train Route (Hybrid)
        # Find nearest stations (simplified logic for prototype)
        # In a real app, uses Google Places API to find nearest station
        origin_station = self._find_nearest_station(origin)
        dest_station = self._find_nearest_station(destination)
        
        train_route = None
        if origin_station and dest_station and origin_station != dest_station:
            # A. Road: Origin -> Origin Station
            leg1 = self.traffic_service.get_travel_time(origin, f"{origin_station} Railway Station")
            leg1_mins = leg1['duration_seconds'] / 60 if 'error' not in leg1 else 15 # fallback 15 mins
            
            # C. Road: Dest Station -> Destination
            leg3 = self.traffic_service.get_travel_time(f"{dest_station} Railway Station", destination)
            leg3_mins = leg3['duration_seconds'] / 60 if 'error' not in leg3 else 10 # fallback 10 mins
            
            # B. Train: Origin Station -> Dest Station
            # We need to arrive at Dest Station by (Arrival Time - Leg3)
            train_arrival_deadline = arrival_dt - timedelta(minutes=leg3_mins)
            
            # Get trains that arrive BEFORE deadline
            # This is reverse search, simplified here:
            # standard search and filter
            trains = self.train_service.get_next_trains(origin_station, dest_station)
            
            best_train = None
            # Find the latest train that reaches before the deadline
            for train in trains:
                t_arr = datetime.strptime(train['arrival'], '%H:%M').time()
                t_arr_dt = datetime.combine(datetime.now().date(), t_arr)
                
                if t_arr_dt <= train_arrival_deadline:
                    best_train = train
                else:
                    break # Assumes trains are sorted by time
            
            if best_train:
                t_dept = datetime.strptime(best_train['departure'], '%H:%M').time()
                t_dept_dt = datetime.combine(datetime.now().date(), t_dept)
                
                # Total leave time = Train Dept - Leg1
                total_leave_dt = t_dept_dt - timedelta(minutes=leg1_mins)
                
                train_route = {
                    'mode': 'Hybrid (Road + Train)',
                    'leave_at': total_leave_dt.strftime('%H:%M'),
                    'details': {
                        'leg1_road': f"Home to {origin_station} Station ({int(leg1_mins)} mins)",
                        'leg2_train': f"{best_train['type']} Train from {origin_station} to {dest_station} ({best_train['departure']} - {best_train['arrival']})",
                        'leg3_road': f"{dest_station} Station to Destination ({int(leg3_mins)} mins)"
                    },
                    'total_duration_mins': (arrival_dt - total_leave_dt).seconds // 60
                }

        road_route = {
            'mode': 'Road Only',
            'leave_at': road_departure_dt.strftime('%H:%M'),
            'details': {
                'summary': f"Drive directly via {road_trip['distance_text']}",
                'duration': road_trip['duration_text']
            },
            'total_duration_mins': int(road_duration_mins)
        }
        
        # Comparison logic
        return {
            'road_route': road_route,
            'train_route': train_route,
            'recommendation': 'Train' if train_route and train_route['total_duration_mins'] < road_route['total_duration_mins'] else 'Road'
        }

    def _find_nearest_station(self, location):
        # Very simple keyword matching for prototype
        for key, station in self.station_map.items():
            if key.lower() in location.lower():
                return station
        return 'Thane' # Default fallback
