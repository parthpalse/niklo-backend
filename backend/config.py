import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ORS_API_KEY = os.getenv('ORS_API_KEY')
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase_credentials.json')
    DEBUG = os.getenv('FLASK_DEBUG', 'True')
