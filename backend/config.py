import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase_credentials.json')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    KJSCE_ADDRESS = 'KJSCE, Vidyavihar West, Mumbai, Maharashtra'
    KJSCE_STATION = 'Vidyavihar'
