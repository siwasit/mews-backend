from fastapi import APIRouter, HTTPException, Depends, Header # type: ignore
from firebase_db import get_firestore_db
from datetime import datetime
import json
from model import MEWSHandling, InspectionsNote, NoteRequest

router = APIRouter()

@router.get('/load_take_in/{user_id}')
def load_take_in(user_id: str): #✅
    db = get_firestore_db()
    
    # Fetch user links for the nurse
    user_link_docs = db.collection('patient_user_links').where("user_id", "==", user_id).stream()
    patient_ids = [doc.to_dict().get('patient_id') for doc in user_link_docs if doc.to_dict().get('patient_id')]

    if not patient_ids:
        raise HTTPException(status_code=404, detail='No patients found for this nurse')

    patient_data_list = []
    for patient_id in patient_ids:
        # Fetch patient data
        patient_doc_ref = db.collection('patients').document(patient_id)
        patient_doc = patient_doc_ref.get()

        if patient_doc.exists:
            patient_data = patient_doc.to_dict()
        else:
            continue  # No patient found for this patient_id, skip

        # Fetch MEWS data for the patient
        mews_docs = db.collection('mews').where('patient_id', '==', patient_id).stream()
        mews_data = [doc.to_dict() for doc in mews_docs]

        # # Fetch InspectionNotes for the patient
        # inspection_docs = db.collection('inspection_notes').where('patient_id', '==', patient_id).stream()
        # inspection_notes = [doc.to_dict() for doc in inspection_docs]

        patient_data_list.append({
            'patient_data': patient_data,
            'mews_data': mews_data,
        })

    return {'patients': patient_data_list}

@router.post('/set_inspection_time/') 
async def time_set(inspection_time: InspectionsNote): #✅
    db = get_firestore_db()

    inspection_note = inspection_time.model_dump()

    # Add patient to Firestore
    doc_ref = db.collection("inspection_notes").add(inspection_note)

    return {"message": "inspection_notes added successfully", "inspection_notes_id": doc_ref[1].id}

@router.post('/add_mews/{inspection_id}')
async def add_mews(mews_data: MEWSHandling, inspection_id: str):  # ✅
    db = get_firestore_db()

    # Add patient to Firestore
    mew_ref = db.collection("mews").add(mews_data.model_dump())

    # Use the original data to set inspection_notes
    note_ref = db.collection("inspection_notes").document(inspection_id)
    note_ref.update({"mews_id": mew_ref[1].id})

    return {"message": "mews_data added successfully", "mews_id": mew_ref[1].id}


@router.post('/add_notes/{note_id}')
async def add_notes(note_id: str, note: NoteRequest): #✅
    db = get_firestore_db()

    # Define the collection and document path using the note_id
    doc_ref = db.collection('inspection_notes').document(note_id)
    
    # Prepare the data to be updated, including only the 'text' and 'time' fields
    note_data = {
        "text": note.text,
        "audit_by": note.audit_by,
    }
    
    # Update the document with the new data (leaves other fields unchanged)
    doc_ref.update(note_data)
    
    return {"message": "Note updated successfully", "note_id": note_id}
    