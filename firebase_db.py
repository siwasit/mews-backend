import firebase_admin
from firebase_admin import credentials, firestore

# Global Firestore client instance
firestore_db = None

def get_firestore_db():
    global firestore_db

    if not firebase_admin._apps:  # Initialize Firebase only once
        cred = credentials.Certificate("mews-project-firebase-adminsdk-fbsvc-1730ff6a5b.json")  # Your Firebase JSON file
        firebase_admin.initialize_app(cred)

    if firestore_db is None:  # Initialize Firestore client only once
        firestore_db = firestore.client()
    
    return firestore_db
