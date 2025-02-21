from fastapi import FastAPI, HTTPException, APIRouter, Request, Response
from firebase_admin import auth
from google.oauth2 import service_account  # ✅ Fix
from google.cloud import firestore
import bcrypt
import firebase_admin
from firebase_admin import credentials
from model import Users, UserAuth, CustomToken
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# Fetch the correct environment variable
firebase_key_path = os.getenv("FIREBASE_ADMINSDK")

if firebase_key_path is None:
    raise ValueError("FIREBASE_ADMINSDK environment variable not set!")

# Initialize Firebase
# ✅ Load Firebase credentials
firebase_cred = credentials.Certificate(firebase_key_path)
firebase_admin.initialize_app(firebase_cred)

app = FastAPI()
router = APIRouter()

# ✅ Load Firestore credentials separately
firestore_credentials = service_account.Credentials.from_service_account_file(firebase_key_path)
db = firestore.Client(credentials=firestore_credentials)  # ✅ Fix

# SESSION_EXPIRE_TIME = 60 * 60 * 24 * 7  # 7 days in seconds
SESSION_EXPIRE_TIME = 300

def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

@router.post("/signup")
async def signup(user: Users): # ✅
    try:
        # Step 1: Manually create Firebase user with Custom UID
        firebase_user = auth.create_user(uid=user.nurse_id, password=user.password)

        # Step 2: Store user details in Firestore
        db.collection("users").document(user.nurse_id).set({
            "uid": firebase_user.uid,
            "fullname": user.fullname,
            "password": hash_password(user.password),  # Hashed password
            "role": user.role  # Assign user role
        })

        # Step 3: Assign Custom Claims (Role)
        auth.set_custom_user_claims(firebase_user.uid, {"role": user.role})

        return {"message": "User created successfully", "firebase_uid": firebase_user.uid}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(user_auth: UserAuth, response: Response):
    try:
        # Step 1: Authenticate the user using UID and password
        user_doc = db.collection("users").document(user_auth.uid).get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = user_doc.to_dict()
        stored_hashed_password = user.get("password")

        # Step 2: Compare the password (hashed)
        if bcrypt.checkpw(user_auth.password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
            
            # Step 3: Create a custom token (for authentication)
            custom_token = auth.create_custom_token(user_auth.uid)
            
            # Send the custom token back to the client
            return {"custom_token": custom_token.decode('utf-8')}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid credentials")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify_session_cookie")
async def verify_session_cookie(session_token: CustomToken):
    session_cookie = session_token.id_token
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Unauthorized: No session cookie")

    try:
        decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
        # print(f"{decoded_claims: }")
        return decoded_claims
    except auth.InvalidSessionCookieError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
@router.post("/create-session-cookie")
async def create_session_cookie(custom_token: CustomToken, response: Response):
    try:
        print(f"Received Token: {custom_token.id_token}")

        # Step 1: Verify the custom token using Firebase's method to get an ID token
        decoded_token = auth.verify_id_token(custom_token.id_token)
        print(f"Decoded Token: {decoded_token}")
        uid = decoded_token['uid']

        print(f"UID: {uid}")

        # Step 2: Create the session cookie using the Firebase ID token (use the token verified above)
        try:
            session_cookie = auth.create_session_cookie(custom_token.id_token, expires_in=SESSION_EXPIRE_TIME)
            print(f"{session_cookie: }")
        except Exception as e:
            print(e)

        print(f"Session cookie: {session_cookie}")
        # Step 3: Set session cookie in the response
        response.set_cookie(
            key="session",
            value=session_cookie,
            httponly=True,  # Prevents JavaScript access
            secure=True,    # Only send over HTTPS
            max_age=SESSION_EXPIRE_TIME
        )

        return {"session_cookie": session_cookie}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session")  # Remove session cookie
    return {"message": "Logged out successfully"}