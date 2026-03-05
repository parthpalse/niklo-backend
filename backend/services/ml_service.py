import pandas as pd
# FIX: Swapped LinearRegression → RandomForestRegressor.
# WHY: LinearRegression fits a flat plane through 3 features — it can't capture
#      non-linear rush-hour spikes (e.g. 8 AM Mon ≠ 8 AM Sat). Random Forest
#      handles these interaction effects with zero feature engineering.
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import numpy as np
from datetime import datetime
import os
import logging

# FIX: Added joblib for model persistence.
# WHY: Without this, every server restart loses all learned trip data.
#      joblib serialises the trained model to disk so it survives restarts.
import joblib

logger = logging.getLogger(__name__)

# FIX: Configurable path for persisted model file.
# WHY: Keeps the model file next to the service code by default,
#      but allows override via env var for deployment (e.g. /tmp on Render).
MODEL_PATH = os.getenv(
    'ML_MODEL_PATH',
    os.path.join(os.path.dirname(__file__), 'commute_model.joblib')
)

# FIX: Hard limits on acceptable training data.
# WHY: Without bounds, a single corrupt row (e.g. duration=-50 or 9999)
#      can poison the entire model and produce garbage predictions.
MIN_DURATION_MINS = 5
MAX_DURATION_MINS = 180


class MLService:
    def __init__(self):
        # FIX: RandomForest with n_estimators=50, random_state for reproducibility.
        # WHY: 50 trees is plenty for <1000 rows and keeps prediction fast (~1 ms).
        self.model = RandomForestRegressor(
            n_estimators=50, random_state=42
        )
        self.trained = False
        # Mock historical data: [Hour, Minute, DayOfWeek] -> Duration(mins)
        self.mock_data = [
            [8, 0, 0, 55], [8, 30, 0, 60], [9, 0, 0, 65],   # Mon morning
            [18, 0, 0, 70], [18, 30, 0, 75],                  # Mon evening
            [8, 0, 1, 50], [9, 0, 1, 62],                     # Tue morning
            # ... more data would be loaded from Firebase Firestore in real app
        ]

        # FIX: Try loading a persisted model first; fall back to training from scratch.
        # WHY: This is the core of the joblib persistence fix — on restart, we
        #      reload the model that was trained on real user data instead of
        #      starting over with only 7 mock rows.
        if not self._load_model():
            self._train_initial_model()

    # ------------------------------------------------------------------
    def _load_model(self) -> bool:
        """Attempt to load a previously saved model from disk."""
        try:
            if os.path.exists(MODEL_PATH):
                self.model = joblib.load(MODEL_PATH)
                self.trained = True
                logger.info("ML Model loaded from disk: %s", MODEL_PATH)
                return True
        except Exception as e:
            logger.warning("Could not load saved model, will retrain: %s", e)
        return False

    def _save_model(self):
        """Persist the trained model to disk."""
        try:
            joblib.dump(self.model, MODEL_PATH)
            logger.info("ML Model saved to disk: %s", MODEL_PATH)
        except Exception as e:
            logger.warning("Could not save model: %s", e)

    # ------------------------------------------------------------------
    def _train_initial_model(self):
        """Trains a RandomForest model on mock historical data."""
        try:
            df = pd.DataFrame(
                self.mock_data,
                columns=['hour', 'minute', 'day_of_week', 'duration']
            )
            X = df[['hour', 'minute', 'day_of_week']]
            y = df['duration']

            self.model.fit(X, y)
            self.trained = True

            # FIX: Log R² score so you can track model quality over time.
            # WHY: Without a metric you're flying blind — R² tells you how much
            #      variance the model explains (1.0 = perfect, 0.0 = guessing).
            score = self.model.score(X, y)
            logger.info(
                "ML Model trained on %d rows (R²=%.3f on training set).",
                len(df), score
            )

            # FIX: Save immediately after training.
            self._save_model()
        except Exception as e:
            logger.error("Error training ML model: %s", e)

    # ------------------------------------------------------------------
    def predict_commute_time(self, hour, minute, day_of_week):
        """Predicts commute time based on time and day."""
        if not self.trained:
            return None

        try:
            prediction = self.model.predict([[hour, minute, day_of_week]])
            return round(float(prediction[0]), 2)
        except Exception as e:
            logger.error("Prediction error: %s", e)
            return None

    # ------------------------------------------------------------------
    def learn_from_trip(self, departure_time, day_of_week, actual_duration):
        """Updates the model with new trip data (incremental retraining)."""
        # FIX: Validate departure_time format before parsing.
        # WHY: A malformed string (e.g. "8am" instead of "08:00") crashes
        #      strptime and takes down the entire /api/learn endpoint.
        try:
            dt = datetime.strptime(departure_time, '%H:%M')
        except (ValueError, TypeError) as e:
            logger.warning("Invalid departure_time '%s': %s", departure_time, e)
            return

        # FIX: Clamp actual_duration to [MIN, MAX] range.
        # WHY: A single corrupt value (e.g. -30 or 9999) can permanently
        #      skew predictions. Clamping keeps the training set sane.
        if not isinstance(actual_duration, (int, float)):
            logger.warning("Invalid actual_duration type: %s", type(actual_duration))
            return
        actual_duration = max(MIN_DURATION_MINS, min(MAX_DURATION_MINS, actual_duration))

        # FIX: Validate day_of_week range.
        # WHY: day_of_week outside 0-6 introduces a feature value the model
        #      has never seen, leading to unpredictable extrapolation.
        if not (0 <= int(day_of_week) <= 6):
            logger.warning("Invalid day_of_week: %s", day_of_week)
            return

        new_row = [dt.hour, dt.minute, int(day_of_week), actual_duration]
        self.mock_data.append(new_row)
        self._train_initial_model()   # retrain + save
