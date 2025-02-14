from fastapi import APIRouter, HTTPException, Depends, Header
from firebase_db import get_firestore_db
from model import PatientData, PatientUserLinks
from datetime import datetime
import pytz

router = APIRouter()

@router.get("/")
def get_patients(): #✅ 
    # Retrieve user from Firestore
    db = get_firestore_db()  # Get Firestore DB client
    patients_ref = db.collection('patients')
    patients = patients_ref.stream()
    
    all_patients = []
    for patient in patients:
        all_patients.append({"patient_id": patient.id, "data": patient.to_dict()})

    if not all_patients:
        raise HTTPException(status_code=404, detail="No users found")

    return {"patients": all_patients}

@router.get("/report/{patient_id}")
def get_report(patient_id: str): #✅ 
    db = get_firestore_db()

    # Fetch patient data from 'patients' collection
    patient_ref = db.collection('patients').document(patient_id)
    patient_doc = patient_ref.get()

    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient_data = patient_doc.to_dict()

    # Fetch related reports from 'mews' collection
    mews_ref = db.collection('mews').where("patient_id", "==", patient_id)
    mews_docs = mews_ref.stream()

    mews_reports = [doc.to_dict() for doc in mews_docs]

    return {
        "patient_id": patient_id,
        "patient_info": patient_data,
        "mews_reports": mews_reports
    }

@router.post("/add_patient/") 
async def add_patient(patient: PatientData): #✅
    db = get_firestore_db()

    utc_now = datetime.now(pytz.utc)
    patient_dict = patient.model_dump()
    patient_dict["created_at"] = utc_now # Ensure created_at is added

    # Add patient to Firestore
    doc_ref = db.collection("patients").add(patient_dict)

    return {"message": "Patient added successfully", "patient_id": doc_ref[1].id}

@router.get("/get_patient/{patient_id}")
async def get_patient_data(patient_id: str):  #✅
    db = get_firestore_db()
    
    patient_ref = db.collection("patients").document(patient_id)
    patient_doc = patient_ref.get()

    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient_data = patient_doc.to_dict()
    
    return {"patient_id": patient_id, "data": patient_data}

@router.put("/update_patient/{patient_id}") #must 'post' every attributes
async def update_patient_data(patient_id: str, patient: PatientData):  #✅
    db = get_firestore_db()
    
    # Get the reference to the existing patient document
    patient_ref = db.collection("patients").document(patient_id)
    
    # Check if the document exists
    patient_doc = patient_ref.get()
    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Update the existing patient document with new data
    patient_ref.update(patient.model_dump())  # Use model_dump() to convert Pydantic model to dict
    
    return {"message": "Patient updated successfully", "patient_id": patient_id}

@router.get("/get-links-by-user/{nurse_id}")
async def get_links_by_user(nurse_id: str): #✅
    db = get_firestore_db()

    # Query to fetch documents where the "uid" field matches the provided uid
    links_ref = db.collection("patient_user_links").where("nurse_id", "==", nurse_id)
    
    # Fetch the documents as a stream
    links = links_ref.stream()

    all_links = []
    for link in links:
        all_links.append({"link_id": link.id, "data": link.to_dict()})

    if not all_links:
        raise HTTPException(status_code=404, detail="No links found for this user")

    return {"message": "Links retrieved successfully", "data": all_links}

@router.post("/take-in/")
async def take_in(patient_user_link: PatientUserLinks): #✅
    db = get_firestore_db()

    link_ref  = db.collection("patient_user_links").add(patient_user_link.model_dump())
    
    link_doc = link_ref[1].get()
    
    if link_doc.exists:
        link_data = link_doc.to_dict()  # Get the data of the document
    else:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Links established successfully", "data": link_data}

@router.delete("/delete-link/{link_id}")
async def delete_link(link_id: str): #✅
    db = get_firestore_db()

    # Get the reference to the document using the link_id
    link_ref = db.collection("patient_user_links").document(link_id)
    
    # Check if the document exists before attempting to delete it
    link_doc = link_ref.get()

    if link_doc.exists:
        # Delete the document
        link_ref.delete()
        return {"message": "Link deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Link not found")
    
@router.get("/get-note/{mews_id}")
async def get_inspection_note(mews_id: str): #✅
    db = get_firestore_db()

    # Query to fetch the inspection note for the specified patient and inspection time
    inspection_ref = db.collection("inspection_notes") \
                        .where("mews_id", "==", mews_id) \
    
    # Fetch the documents as a stream
    inspection_notes = inspection_ref.stream()

    # Initialize a list to hold all found notes
    notes = []
    for note in inspection_notes:
        notes.append({"note_id": note.id, "data": note.to_dict()})

    if not notes:
        raise HTTPException(status_code=404, detail="No inspection note found for this patient and time")

    return {"message": "Inspection note retrieved successfully", "data": notes}
