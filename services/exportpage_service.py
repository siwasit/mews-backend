from fastapi import APIRouter, HTTPException, Depends, Header # type: ignore
from firebase_db import get_firestore_db
from model import PatientData
from fastapi.responses import StreamingResponse # type: ignore
import pandas as pd # type: ignore
import io

router = APIRouter()

@router.get('/patient_load/{patient_id}')
async def patient_load(patient_id: str):
    db = get_firestore_db()
    
    try:
        doc = db.collection('patients').document(patient_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Patient not found")

        patient = doc.to_dict()
        patient['patient_id'] = doc.id

        return {"status": "Success!", "data": patient}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get('/filter')
async def filter(patients: PatientData):
    db = get_firestore_db()
    patient_ref = db.collection('patients')

    try: 
        query = patient_ref
        if patients.age:
            query = query.where("age", '==', patients.age)
        if patients.name:
            query = query.where("name", '==', patients.name)
        if patient.lastname:
            query = query.where("lastname", "==", patient.lastame)

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

@router.post('/get_report_excel')
async def get_report_excel(patient_id: str):
    db = get_firestore_db()

    try:
        # Fetch patient data
        patient_ref = db.collection('patients').document(patient_id).get()
        if not patient_ref.exists:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient_data = patient_ref.to_dict()
        patient_data['patient_id'] = patient_id

        # Fetch MEWS data 
        mews_ref = db.collection('MEWS').where("patient_id", "==", patient_id)
        mews_docs = mews_ref.stream()
        mews_data = [doc.to_dict() for doc in mews_docs]

        # Combine into a DataFrame
        patient_df = pd.DataFrame([patient_data])
        mews_df = pd.DataFrame(mews_data)

        # Merge data
        report_df = pd.concat([patient_df, mews_df], ignore_index=True)

        # Convert to Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            report_df.to_excel(writer, index=False, sheet_name="Report")

        output.seek(0)

        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": "attachment; filename=patient_report.xlsx"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))