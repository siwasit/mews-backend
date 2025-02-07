from fastapi import FastAPI, HTTPException, Header, Depends
from firebase_auth import verify_firebase_token  # Firebase authentication
from firebase_db import db, add_data, get_data, get_all_data, update_data, delete_data
import uuid

app = FastAPI()

# Middleware to authenticate users with Firebase token
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No auth token provided")

    token = authorization.split(" ")[1]  # Extract token from "Bearer <TOKEN>"
    user = verify_firebase_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user

### ✅ USER ENDPOINTS ###
@app.get("/users/me")
def get_me(user: dict = Depends(get_current_user)):
    return {"uid": user["uid"], "email": user["email"], "name": user.get("name", "Unknown")}

@app.get("/users/{uid}")
def get_user(uid: str):
    user = get_data("users", uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

### ✅ PATIENT ENDPOINTS ###
@app.post("/patients")
def add_patient(fullname: str, gender: str, age: int):
    patient_id = str(uuid.uuid4())
    patient_data = {"fullname": fullname, "gender": gender, "age": age}
    add_data("patients", patient_id, patient_data)
    return {"patient_id": patient_id, **patient_data}

@app.get("/patients")
def list_patients():
    return get_all_data("patients")

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    patient = get_data("patients", patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

### ✅ MEWS SCORE ENDPOINTS ###
@app.post("/mews")
def add_mews(patient_id: str, heart_rate: int, mews_score: int):
    mews_id = str(uuid.uuid4())
    mews_data = {"patient_id": patient_id, "heart_rate": heart_rate, "mews_score": mews_score}
    add_data("mews", mews_id, mews_data)
    return {"mews_id": mews_id, **mews_data}

@app.get("/mews/{patient_id}")
def get_mews(patient_id: str):
    all_mews = get_all_data("mews")
    return {key: value for key, value in all_mews.items() if value["patient_id"] == patient_id}

### ✅ INSPECTION NOTES ENDPOINTS ###
@app.post("/notes")
def add_note(patient_id: str, text: str):
    note_id = str(uuid.uuid4())
    note_data = {"patient_id": patient_id, "text": text}
    add_data("notes", note_id, note_data)
    return {"note_id": note_id, **note_data}

@app.get("/notes/{patient_id}")
def get_notes(patient_id: str):
    all_notes = get_all_data("notes")
    return {key: value for key, value in all_notes.items() if value["patient_id"] == patient_id}