from fastapi import APIRouter, HTTPException, Depends, Header # type: ignore
from firebase_db import get_firestore_db
from datetime import datetime
import json
from model import Users, Token

router = APIRouter()

@router.get('/{uid}')
async def load_take_in(uid: str):
    db = get_firestore_db()
    user_link_ref = db.collection('patient_user_link').document(uid)
    user_link_doc = user_link_ref.get()
    
    if not user_link_doc.exists:
        raise HTTPException(status_code=404, detail='User not found in patient_user_link')
    
    patient_id = user_link_doc.to_dict().get('patient_id')
    if not patient_id:
        raise HTTPException(status_code=404, detail='patient_id not found')
    
    patient_ref = db.collection('patients').document(patient_id)
    patient_doc = patient_ref.get()

    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail='Patient data not found')
    
    patient_stream = db.collection('patients').stream()
    patient_list = [doc.to_dict() for doc in patient_stream]

    return {'data': patient_list}

@router.post('/inspection_notes')
async def time_set(uid: str, inspection_time: datetime):
    db = get_firestore_db()
    user_link_ref = db.collection('patient_user_link').document(uid)
    user_link_doc = user_link_ref.get()
    
    if not user_link_doc.exists:
        raise HTTPException(status_code=404, detail="User not found in patient_user_link")
    
    patient_id = user_link_doc.to_dict().get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=404, detail="patient_id not found for this user")
    
    inspection_ref = db.collection('inspection_notes').document(patient_id)
    inspection_ref.set({"inspection_time": inspection_time.isoformat()}, merge=True)
    
    return {"message": "Inspection time updated successfully", "inspection_time": inspection_time.isoformat()}


async def add_mews(patient_id: str, uid: str, mews_data: MEWS):
    db = get_firestore_db()
    collection_ref = db.collection("MEWS")

    required_fields = {"mews_score", "heart_rate", "respiratory_rate", "temperature", "blood_pressure", "consciousness", "spo2"}
    if not required_fields.issubset(data.keys()):
        raise HTTPException(status_code=400, detail=json.dumps({"error": f"Missing required fields: {list(required_fields - data.keys())}"}))
    
    entry = {
        "patient_id": patient_id,
        "uid": uid,
        "score": mews_data["score"],
        "heart_rate": mews_data["heart_rate"],
        "respiratory_rate": mews_data["respiratory_rate"],
        "temperature": mews_data["temperature"],
        "blood_pressure": mews_data["blood_pressure"],
        "consciousness": mews_data["consciousness"],
        "spo2": mews_data["spo2"],
        "created_at": datetime.utcnow().isoformat()
    }
    
    doc_ref = collection_ref.add(entry)
    return doc_ref

@router.post('/add_note/{patient_id}')
async def add_notes(patient_id: str, text: str):
    db = get_firestore_db()
    text_ref = db.collection('text').document(patient_id)

    try:
        text_ref.set({"Inspection_notes": text}, merge=True)
        return {"message": "Notes added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
