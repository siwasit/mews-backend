from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks # type: ignore
from firebase_db import get_firestore_db
from model import PatientData, PatientIDRequest
from fastapi.responses import StreamingResponse # type: ignore
import pandas as pd # type: ignore
import io
from utils.excel_decorator import ExcelDecorator, FirstRowDeleter, Decorator
from utils.report_generate import generate_patient_report
from fastapi.responses import FileResponse
import os
from openpyxl.styles import Border, Side
from openpyxl import load_workbook
from datetime import datetime

router = APIRouter()

def convert_firestore_timestamps(data):
    """Convert Firestore Timestamps (datetime) to timezone-naive datetime."""
    if isinstance(data, dict):  # Check if data is a dictionary
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.replace(tzinfo=None)
    elif isinstance(data, list): # Check if it is a list
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.replace(tzinfo=None)
    return data

def enforce_datetime(df):
    for column in df.columns:
        if pd.api.types.is_object_dtype(df[column]):
            try:
                df[column] = pd.to_datetime(df[column], errors="ignore")
            except (ValueError, TypeError):  # Catch potential errors during conversion
                pass  # Ignore if conversion fails
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.tz_localize(None)
    return df

def delete_file(file_path: str):
    """Function to delete the file."""
    os.remove(file_path)

@router.get('/patient_load')
def get_patients():  # ✅ 
    # Retrieve user from Firestore
    db = get_firestore_db()  # Get Firestore DB client
    patients_ref = db.collection('patients')
    patients = patients_ref.stream()

    all_patients = []

    for patient in patients:
        patient_data = patient.to_dict()  # Convert document to dictionary
        patient_data['patient_id'] = patient.id  # Include document ID if needed
        all_patients.append(patient_data)

    return {"patients": all_patients}
    
# @router.get('/filter') # รับ JSON ID ของผู้ป่วย ที่ Filter เบื้องต้นได้
# def filter(patients_filter: PatientFilter):
#     db = get_firestore_db()
#     #mews by id
#     #patient by

@router.post('/get_report_excel')  # Use POST for request body
async def get_report_excel(patient_ids: dict, background_tasks: BackgroundTasks):
    db = get_firestore_db()
    is_mews_and_note_empty: bool = False 
    
    try:
        all_reports_data = {}  # Store data for all patients

        for patient_id in patient_ids.get("patient_ids", []):  # Access the list of IDs
            try:  # Inner try-except for each patient
                patient_ref = db.collection('patients').document(patient_id)
                patient_doc = patient_ref.get()

                if not patient_doc.exists:
                    print(f"Patient {patient_id} not found.")  # Log, but continue with other patients
                    continue  # Skip to the next patient

                patient_data = convert_firestore_timestamps(patient_doc.to_dict())
                patient_data['patient_id'] = patient_doc.id

                # ... (fetch mews and notes data - same as in get_report)
                mews_ref = db.collection('mews').where("patient_id", "==", patient_doc.id)
                mews_docs = list(mews_ref.stream())
                mews_data = []
                if len(mews_docs) != 0:
                    for doc in mews_docs:
                        mews_dict = doc.to_dict()
                        mews_dict["mews_id"] = doc.id
                        mews_data.append(convert_firestore_timestamps(mews_dict))
               

                note_ref = db.collection('inspection_notes').where("patient_id", "==", patient_doc.id)
                note_docs = list(note_ref.stream())
                note_data = [convert_firestore_timestamps(doc.to_dict()) for doc in note_docs]

                report_data = []
                patient_df = pd.DataFrame([patient_data])
                patient_df = enforce_datetime(patient_df)
                gender = '-'
                if patient_data['gender'] == 'Male':
                    gender = 'ชาย'
                elif patient_data['gender'] == 'Female':
                    gender = 'หญิง'
                report_data.append(['ชื่อ-นามสกุล', patient_data['fullname']])
                report_data.append(['อายุ', patient_data['age'], 'เพศ', gender])
                report_data.append(['หมายเลขเตียง', patient_data['bed_number']])
                report_data.append(['หมายเลขโรงพยาบาล', patient_data['hospital_number']])
                report_data.append(['หอผู้ป่วย', patient_data['ward']])
                report_data.append([''])

                report_data.append(['วันเวลา', 'C', 'T', 'P', 'R', 'BP', 'O2 Sat', 'Urine', 'Total Score (MEWS)', 'CVP', 'หมายเหตุ', 'แก้ไขโดย'])
                
                mews_df = pd.DataFrame(mews_data)
                note_df = pd.DataFrame(note_data)
                mews_df = enforce_datetime(mews_df)
                note_df = enforce_datetime(note_df)
                
                if len(mews_data) != 0 and len(note_data) != 0:
                    merged_df = pd.merge(mews_df, note_df, on="mews_id", how="inner")
                    merged_df = merged_df.sort_values(by='time', ascending=True)
                    auditor_ids = merged_df["audit_by"].unique()
                    auditor_docs = {
                        user_id: db.collection("users").document(user_id).get().to_dict().get("fullname", "Unknown")
                        for user_id in auditor_ids if user_id is not None
                    }
                    merged_df["auditor_name"] = merged_df["audit_by"].map(auditor_docs)
                    for _, row in merged_df.iterrows():
                        report_data.append([
                            row['time'], row['consciousness'], row['temperature'], row['heart_rate'],
                            row['respiratory_rate'], row['blood_pressure'], row['spo2'], row['urine'],
                            row['mews'], '-', row['text'], row['auditor_name']
                        ])

                    
                else:
                    is_mews_and_note_empty = True
                    merged_df = pd.DataFrame()

                report_df = pd.DataFrame(report_data)
                patient_name = patient_data['fullname'].replace(' ', '_')
                all_reports_data[patient_name] = [report_df, is_mews_and_note_empty]

            except Exception as inner_e:
                print(f"Error processing patient {patient_id}: {inner_e}")  # Log individual patient errors

        if not all_reports_data: # If no report data is generated
            return {"message": "No report data found"}, 404

        os.makedirs('temp', exist_ok=True)
        filepath = "temp/all_patients_report.xlsx"  # Common filename for all reports

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            iters = []  # Collect sheet names and flags
            for sheet_name, data in all_reports_data.items():
                df, is_empty = data  # Unpack the tuple
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                iters.append((sheet_name, is_empty))  # Store sheet name and empty flag

        # NOW that the file is written, modify it
        for sheet_name, is_empty in iters:
            if is_empty:
                deleter = FirstRowDeleter(filepath, sheet_name)
                deleter.del_first_row()
                decorator = Decorator(filepath, sheet_name)
                decorator.decorate()

        decorator = ExcelDecorator(filepath)
        decorator.decorate()

        def iter_file():
            with open(filepath, mode="rb") as file:
                yield from file

        background_tasks.add_task(delete_file, filepath)
        return StreamingResponse(iter_file(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={os.path.basename(filepath)}"})

    except Exception as e:
        print(f"Error in get_reports: {e}")
        raise