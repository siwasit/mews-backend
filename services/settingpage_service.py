from fastapi import APIRouter, HTTPException, Depends, Header
from firebase_db import get_firestore_db
# from firebase_auth import verify_firebase_token

router = APIRouter()