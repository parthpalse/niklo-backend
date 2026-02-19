from datetime import datetime, timedelta

class TrainService:
    def __init__(self):
        # Mock data for Thane (Central Line)
        # In a real app, this would scrape mIndicator or use a railway API
        self.stations = ['CSMT', 'Dadar', 'Kurla', 'Ghatkopar', 'Thane', 'Dombivli', 'Kalyan']
        self.schedules = self._generate_mock_schedule()

    def _generate_mock_schedule(self):
        """Generates a realistic mock schedule for trains."""
        schedule = []
        start_time = datetime.now().replace(hour=4, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=20) # Untill midnight
        
        current_time = start_time
        while current_time < end_time:
            # Fast train: CSMT -> Thane in ~40 mins
            schedule.append({
                'train_id': f"F{current_time.strftime('%H%M')}",
                'type': 'Fast',
                'source': 'CSMT',
                'destination': 'Kalyan',
                'stations': {
                    'CSMT': current_time.strftime('%H:%M'),
                    'Dadar': (current_time + timedelta(minutes=10)).strftime('%H:%M'),
                    'Kurla': (current_time + timedelta(minutes=18)).strftime('%H:%M'),
                    'Ghatkopar': (current_time + timedelta(minutes=24)).strftime('%H:%M'),
                    'Thane': (current_time + timedelta(minutes=40)).strftime('%H:%M'),
                    'Dombivli': (current_time + timedelta(minutes=55)).strftime('%H:%M'),
                    'Kalyan': (current_time + timedelta(minutes=65)).strftime('%H:%M'),
                }
            })
            
            # Slow train: CSMT -> Thane in ~55 mins (every 10 mins)
            current_time += timedelta(minutes=5) 
            schedule.append({
                'train_id': f"S{current_time.strftime('%H%M')}",
                'type': 'Slow',
                'source': 'CSMT',
                'destination': 'Kalyan',
                'stations': {
                    'CSMT': current_time.strftime('%H:%M'),
                    'Dadar': (current_time + timedelta(minutes=15)).strftime('%H:%M'),
                    'Thane': (current_time + timedelta(minutes=55)).strftime('%H:%M'),
                    # Simplified for brevity
                }
            })
            current_time += timedelta(minutes=5)
            
        return schedule

    def get_next_trains(self, source, destination, time_str=None):
        """
        Finds the next available trains from source to destination after a given time.
        """
        if time_str:
            query_time = datetime.strptime(time_str, '%H:%M').time()
        else:
            query_time = datetime.now().time()

        next_trains = []
        for train in self.schedules:
            if source in train['stations'] and destination in train['stations']:
                dept_time_str = train['stations'][source]
                dept_time = datetime.strptime(dept_time_str, '%H:%M').time()
                
                # Check if train is after query time
                if dept_time >= query_time:
                    arrival_time_str = train['stations'][destination]
                    
                    # Calculate duration
                    dept_dt = datetime.combine(datetime.today(), dept_time)
                    arr_dt = datetime.combine(datetime.today(), datetime.strptime(arrival_time_str, '%H:%M').time())
                    duration_mins = (arr_dt - dept_dt).seconds // 60
                    
                    next_trains.append({
                        'train_id': train['train_id'],
                        'type': train['type'],
                        'departure': dept_time_str,
                        'arrival': arrival_time_str,
                        'duration_mins': duration_mins
                    })
                    
                    if len(next_trains) >= 5: # Return top 5
                        break
                        
        return next_trains
