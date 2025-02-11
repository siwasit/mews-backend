from fastapi import APIRouter, HTTPException, Depends, Header
from firebase_db import get_firestore_db
from model import PatientData

router = APIRouter()

@router.get('/patient_load/{patient_id}')
async def patient_load(patient_id: str):
    db = get_firestore_db()
    patient_ref = db.collection('patients').limit(10)

    try:
        patient_data = []
        docs = patient_ref.stream()

        for doc in docs:
            patient = doc.to_dict()
            patient['patient_id'] = doc.id
            patient_data.append(patient)

        return {"status": "Success!", "data": patient_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get('/filter')
async def filter(patients: PatientData):
    db = get_firestore_db()
    patient_ref = db.collection('patients')

    try: 
        query = patient_ref
        if patients['age']:
            query = query.where("age", '==', patients['age'])
        if patients['name']:
            query = query.where("name", '==', patients['name'])
        if patient['lastname']:
            query = query.where("lastname", "==", patient['lastname'])

        query = query.limit(10)
        patients_data = []
        docs = query.stream()

        for doc in docs:
            patient = doc.to_dict()
            patient["patient_id"] = doc.id  
            patients_data.append(patient)

        return {"status": "Success!", "data": patients_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/')
async def get_report_excel():
    pass