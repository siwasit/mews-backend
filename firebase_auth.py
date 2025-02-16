import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# Fetch the correct environment variable
firebase_key_path = os.getenv("FIREBASE_ADMINSDK")

if firebase_key_path is None:
    raise ValueError("FIREBASE_ADMINSDK environment variable not set!")

def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_key_path)
        firebase_admin.initialize_app(cred)

def verify_firebase_token(token: str):
    try:
        # Decoding the token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
