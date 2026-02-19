import firebase_admin
from firebase_admin import credentials, messaging
from config import Config
import os

class NotificationService:
    def __init__(self):
        self.initialized = False
        try:
            if os.path.exists(Config.FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                self.initialized = True
                print("Firebase Admin Initialized Successfully")
            else:
                print(f"Warning: Firebase credentials not found at {Config.FIREBASE_CREDENTIALS_PATH}. Notifications will be disabled.")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")

    def send_push_notification(self, token, title, body):
        if not self.initialized:
            return {'error': 'Firebase not initialized'}

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                token=token,
            )
            response = messaging.send(message)
            return {'success': True, 'message_id': response}
        except Exception as e:
            return {'error': str(e)}
