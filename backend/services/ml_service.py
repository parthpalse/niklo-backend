import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np
from datetime import datetime

class MLService:
    def __init__(self):
        self.model = LinearRegression()
        self.trained = False
        # Mock historical data: [Hour, Minute, DayOfWeek] -> Duration(mins)
        self.mock_data = [
            [8, 0, 0, 55], [8, 30, 0, 60], [9, 0, 0, 65], # Mon morning
            [18, 0, 0, 70], [18, 30, 0, 75], # Mon evening
            [8, 0, 1, 50], [9, 0, 1, 62], # Tue morning
            # ... more data would be loaded from Firebase Firestore in real app
        ]
        self._train_initial_model()

    def _train_initial_model(self):
        """Trains a simple regression model on mock historical data."""
        try:
            df = pd.DataFrame(self.mock_data, columns=['hour', 'minute', 'day_of_week', 'duration'])
            X = df[['hour', 'minute', 'day_of_week']]
            y = df['duration']
            
            self.model.fit(X, y)
            self.trained = True
            print("ML Model trained on initial mock data.")
        except Exception as e:
            print(f"Error training ML model: {e}")

    def predict_commute_time(self, hour, minute, day_of_week):
        """Predicts commute time based on time and day."""
        if not self.trained:
            return None
            
        try:
            prediction = self.model.predict([[hour, minute, day_of_week]])
            return round(prediction[0], 2)
        except Exception as e:
            print(f"Prediction error: {e}")
            return None

    def learn_from_trip(self, departure_time, day_of_week, actual_duration):
        """Updates the model with new trip data (Incremental learning or retraining)."""
        # In a real app, save this to Firestore, then periodically retrain.
        # Here we just append to mock_data and retrain immediately for demo.
        dt = datetime.strptime(departure_time, '%H:%M')
        new_row = [dt.hour, dt.minute, day_of_week, actual_duration]
        self.mock_data.append(new_row)
        self._train_initial_model()
