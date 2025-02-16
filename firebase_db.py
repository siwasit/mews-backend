import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# Fetch the correct environment variable
firebase_key_path = os.getenv("FIREBASE_ADMINSDK")

if firebase_key_path is None:
    raise ValueError("FIREBASE_ADMINSDK environment variable not set!")

# Global Firestore client instance
firestore_db = None

def get_firestore_db():
    global firestore_db

    if not firebase_admin._apps:  # Initialize Firebase only once
        cred = credentials.Certificate(firebase_key_path)  # Your Firebase JSON file
        firebase_admin.initialize_app(cred)

    if firestore_db is None:  # Initialize Firestore client only once
        firestore_db = firestore.client()
    
    return firestore_db
