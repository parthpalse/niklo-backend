import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ORS_API_KEY = os.getenv('ORS_API_KEY')
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase_credentials.json')
    # Correctly parsed as a boolean (was previously always True as a string)
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    # KJSCE Vidyavihar — hardcoded end destination for all commute calculations
    KJSCE_ADDRESS = 'KJSCE, Vidyavihar West, Mumbai, Maharashtra'
    KJSCE_STATION = 'Vidyavihar'
