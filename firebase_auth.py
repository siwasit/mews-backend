import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException

def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("mews-project-firebase-adminsdk-fbsvc-1730ff6a5b.json")
        firebase_admin.initialize_app(cred)

def verify_firebase_token(token: str):
    try:
        # Decoding the token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
