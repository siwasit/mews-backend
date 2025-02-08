from fastapi import APIRouter, HTTPException, Depends, Header
from firebase_db import get_firestore_db
# from firebase_auth import verify_firebase_token


# # Helper function to extract token from headers
# def get_token_from_header(authorization: str = Header(...)):
#     # This automatically extracts the 'Authorization' header
#     token = authorization.split("Bearer ")[-1]  # Extract token from 'Bearer <token>'
#     return token

# @router.post("/add")
# async def add_user(user_data: dict, authorization: str = Depends(get_token_from_header)):
#     # Verify Firebase token
#     decoded_token = verify_firebase_token(authorization) ##ใช้ Access uid
    
#     # Now that the user is verified, you can add data to Firestore
#     db = get_firestore_db()  # Get Firestore DB client
#     doc_ref = db.collection('users').document()  # Add user to 'users' collection
#     doc_ref.set(user_data)

#     return {"message": "User added successfully", "data": doc_ref.get().to_dict()}

router = APIRouter()