from fastapi import APIRouter, HTTPException, Depends, Header # type: ignore
from firebase_db import get_firestore_db
from datetime import datetime
import json
from model import Users, Token, MEWS, InspectionsNote

router = APIRouter()

@router.get('/load_take_in/{nurse_id}')
def load_take_in(nurse_id: str):
    db = get_firestore_db()
    
    # Fetch user links for the nurse
    user_link_docs = db.collection('patient_user_links').where("nurse_id", "==", nurse_id).stream()
    patient_ids = [doc.to_dict().get('patient_id') for doc in user_link_docs if doc.to_dict().get('patient_id')]

    if not patient_ids:
        raise HTTPException(status_code=404, detail='No patients found for this nurse')

    patient_data_list = []
    for patient_id in patient_ids:
        # Fetch patient data
        patient_ref = db.collection('patients').where('patient_id', '==', patient_id)
        patient_doc = patient_ref.get()

        # Fetch MEWS data for the patient
        mews_docs = db.collection('mews').where('patient_id', '==', patient_id).stream()
        mews_data = [doc.to_dict() for doc in mews_docs]
        print(f'DOC: {mews_data}')

        # Fetch InspectionNotes for the patient
        inspection_docs = db.collection('inspection_notes').where('patient_id', '==', patient_id).stream()
        inspection_notes = [doc.to_dict() for doc in inspection_docs]

        patient_data_list.append({
            'patient_data': patient_doc.to_dict(),
            'mews_data': mews_data,
            'inspection_notes': inspection_notes
        })

    return {'patients': patient_data_list}

@router.post('/set_inspection_time')
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

@router.post('/add_mews/{patient_id}') ###ยังไม่ผ่าน
async def add_mews(patient_id: str, uid: str, mews_data: MEWS):
    db = get_firestore_db()
    collection_ref = db.collection("MEWS")

    required_fields = {"mews_score", "heart_rate", "respiratory_rate", "temperature", "blood_pressure", "consciousness", "spo2", "urine"}
    if not required_fields.issubset(mews_data.keys()):
        raise HTTPException(status_code=400, detail=json.dumps({"error": f"Missing required fields: {list(required_fields - mews_data.keys())}"}))
    
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
        "urine": mews_data['urine'],
        "created_at": datetime.utcnow().isoformat()
    }
    
    doc_ref = collection_ref.add(entry)
    return doc_ref

@router.post('/add_notes/{patient_id}')
async def add_notes(patient_id: str, text: str): ###ยังไม่ผ่าน อาจต้องเปลี่ยน parameter
    db = get_firestore_db()
    text_ref = db.collection('text').document(patient_id)
    ###ยังไม่ผ่าน ขาด uid กับ mews_id
    try:
        text_ref.set({"Inspection_notes": text}, merge=True)
        return {"message": "Notes added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
