from fastapi import FastAPI, HTTPException, APIRouter, Request, Response
from firebase_admin import auth
from google.cloud import firestore
import bcrypt
import firebase_admin
from firebase_admin import credentials

# Initialize Firebase
cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

app = FastAPI()
router = APIRouter()
db = firestore.Client()

SESSION_EXPIRE_TIME = 60 * 60 * 24 * 7  # 7 days in seconds

def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

@router.post("/signup/")
async def signup(user_id: str, password: str, role: str = "user"):
    try:
        # Step 1: Manually create Firebase user with Custom UID
        user = auth.create_user(uid=user_id)

        # Step 2: Store user details in Firestore
        db.collection("users").document(user_id).set({
            "uid": user.uid,
            "password": hash_password(password),  # Hashed password
            "role": role  # Assign user role
        })

        # Step 3: Assign Custom Claims (Role)
        auth.set_custom_user_claims(user.uid, {"role": role})

        return {"message": "User created successfully", "firebase_uid": user.uid}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login/")
async def login(request: Request, response: Response):
    body = await request.json()
    id_token = body.get("idToken")  # Get ID token from frontend

    try:
        # Generate session cookie
        session_cookie = auth.create_session_cookie(id_token, expires_in=SESSION_EXPIRE_TIME)

        # Set session cookie in the response
        response.set_cookie(
            key="session",
            value=session_cookie,
            httponly=True,  # Prevents JavaScript access
            secure=True,    # Only send over HTTPS
            max_age=SESSION_EXPIRE_TIME
        )

        return {"message": "Session created"}
    
    except Exception as e:
        return {"error": str(e)}
    
@router.get("/protected-route/")
async def protected_route(request: Request):
    session_cookie = request.cookies.get("session")  # Get session cookie

    if not session_cookie:
        return {"error": "Unauthorized"}, 401

    try:
        # Verify session
        decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
        return {"message": "Access granted", "user_id": decoded_claims["uid"]}
    
    except auth.InvalidSessionCookieError:
        return {"error": "Invalid session"}, 401

@app.post("/logout/")
async def logout(response: Response):
    response.delete_cookie("session")  # Remove session cookie
    return {"message": "Logged out"}


###-------------------------ของ โอ๊ต--------------------------##
# firebase.auth().signInWithCustomToken(customToken)
#   .then((userCredential) => {
#     console.log("User signed in", userCredential.user);
#   })
#   .catch((error) => {
#     console.error("Login failed", error);
#   });
###-------------------------ของ โอ๊ต--------------------------##

# from fastapi import HTTPException, Depends, APIRouter
# from pydantic import BaseModel
# from passlib.context import CryptContext
# from datetime import datetime, timedelta
# from jose import JWTError, jwt # type: ignore
# from model import Users, Token
# from firebase_db import get_firestore_db

# SECRET_KEY = "your-secret-key"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# router = APIRouter()

# # Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # Generate JWT Token
# def create_access_token(nurse_id: str):
#     expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode = {"sub": nurse_id, "exp": expire}
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# # Decode JWT Token
# def verify_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload["sub"]
#     except JWTError:
#         return None

# # Dependency for Protected Routes
# def get_current_user(token: str):
#     nurse_id = verify_token(token)
#     if not nurse_id:
#         raise HTTPException(status_code=401, detail="Invalid token")
#     return nurse_id

# # Register User
# @router.post("/register")
# async def register(user: Users):
#     db = get_firestore_db()
#     user_ref = db.collection("users").document(user.nurse_id).get()
#     if user_ref.exists:
#         raise HTTPException(status_code=400, detail="Nurse ID already registered")
    
#     hashed_password = pwd_context.hash(user.password)
#     db.collection("users").document(user.nurse_id).set({
#         "nurse_id": user.nurse_id,
#         "password": hashed_password
#     })

#     return {"message": "User registered successfully", "nurse_id": user.nurse_id}

# # Login User
# @router.post("/login", response_model=Token)
# async def login(user: Users):
#     db_user = Users.get(user.nurse_id)
    
#     if not db_user or not pwd_context.verify(user.password, db_user["password"]):
#         raise HTTPException(status_code=401, detail="Invalid credentials")
    
#     access_token = create_access_token(db_user["nurse_id"])
#     return {"access_token": access_token, "token_type": "bearer"}

# # Protected Route (Requires Authentication)
# @router.get("/protected")
# async def protected_route(nurse_id: str = Depends(get_current_user)):
#     return {"message": "Welcome!", "nurse_id": nurse_id}