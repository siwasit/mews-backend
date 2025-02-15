from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks # type: ignore
from firebase_db import get_firestore_db
from model import PatientData, PatientIDRequest
from fastapi.responses import StreamingResponse # type: ignore
import pandas as pd # type: ignore
import io
from utils.excel_decorator import ExcelDecorator
from utils.report_generate import generate_patient_report
from fastapi.responses import FileResponse
import os
from openpyxl.styles import Border, Side
from openpyxl import load_workbook

router = APIRouter()

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

@router.get('/get_report_excel_ind/{patient_id}')
def get_report_excel(patient_id: str, background_tasks: BackgroundTasks): # ✅
    db = get_firestore_db()

    try:
        # Fetch patient data
        patient_ref = db.collection('patients').document(patient_id).get()
        if not patient_ref.exists:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient_data = patient_ref.to_dict()
        patient_data['patient_id'] = patient_id

        # Fetch MEWS data 
        mews_ref = db.collection('mews').where("patient_id", "==", patient_id)
        mews_docs = mews_ref.stream()
        mews_data = [{"mews_id": doc.id, **doc.to_dict()} for doc in mews_docs]

        note_ref = db.collection('inspection_notes').where("patient_id", "==", patient_id)
        note_docs = note_ref.stream()
        note_data = [doc.to_dict() for doc in note_docs]

        # Combine into a DataFrame
        patient_df = pd.DataFrame([patient_data])
        mews_df = pd.DataFrame(mews_data)
        note_df = pd.DataFrame(note_data)
        
        # Handle timezone-aware datetimes
        def strip_timezone(df):
            for column in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[column]):
                    df[column] = df[column].dt.tz_localize(None)  # Remove timezone info
            return df

        # Strip timezone from both patient and mews data if necessary
        patient_df = strip_timezone(patient_df)
        mews_df = strip_timezone(mews_df)
        note_df = strip_timezone(note_df)

        auditor_dict = {}
        for user_id in note_df["audit_by"].unique().tolist():
            user_ref = db.collection("users").document(user_id).get()
            if user_ref.exists:
                auditor_dict[user_id] = user_ref.to_dict().get("fullname", "Unknown")

        note_df["auditor_name"] = note_df["audit_by"].map(auditor_dict)

        # Create an empty DataFrame for patient details
        df1 = pd.DataFrame(columns=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'])

        # Assign patient data (assuming only one row per patient)
        df1.loc[0, 'A'] = 'ชื่อ-นามสกุล'
        df1.loc[0, 'B'] = patient_df['fullname'].iloc[0]

        df1.loc[1, 'A'] = 'อายุ'
        df1.loc[1, 'B'] = patient_df['age'].iloc[0]
        df1.loc[1, 'C'] = 'เพศ'
        df1.loc[1, 'D'] = patient_df['gender'].iloc[0]

        df1.loc[2, 'A'] = 'หมายเลขเตียง'
        df1.loc[2, 'B'] = patient_df['bed_number'].iloc[0]

        df1.loc[3, 'A'] = 'หมายเลขโรงพยาบาล'
        df1.loc[3, 'B'] = patient_df['hospital_number'].iloc[0]

        df1.loc[4, 'A'] = 'หอผู้ป่วย'
        df1.loc[4, 'B'] = patient_df['ward'].iloc[0]

        df1.loc[5, 'A'] = ''

        # Create an empty DataFrame for vital signs
        df2 = pd.DataFrame(columns=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'])

        # Assign column headers
        df2.loc[0] = ['วันเวลา', 'C', 'T', 'P', 'R', 'BP', 'O2 Sat', 'Urine', 'Total Score (MEWs)', 'CVP', 'หมายเหตุ', 'แก้ไขโดย']

        merged_df = pd.merge(mews_df, note_df, on="mews_id", how="inner")
        merged_df = merged_df.sort_values(by='time', ascending=True)

        for i in range(len(merged_df)):
            df2.loc[i + 1, 'A'] = merged_df['time'].iloc[i] if pd.notna(merged_df['time'].iloc[i]) else "-"
            df2.loc[i + 1, 'B'] = merged_df['consciousness'].iloc[i] if pd.notna(merged_df['consciousness'].iloc[i]) else "-"
            df2.loc[i + 1, 'C'] = merged_df['temperature'].iloc[i] if pd.notna(merged_df['temperature'].iloc[i]) else "-"
            df2.loc[i + 1, 'D'] = merged_df['heart_rate'].iloc[i] if pd.notna(merged_df['heart_rate'].iloc[i]) else "-"
            df2.loc[i + 1, 'E'] = merged_df['respiratory_rate'].iloc[i] if pd.notna(merged_df['respiratory_rate'].iloc[i]) else "-"  
            df2.loc[i + 1, 'F'] = merged_df['blood_pressure'].iloc[i] if pd.notna(merged_df['blood_pressure'].iloc[i]) else "-"
            df2.loc[i + 1, 'G'] = merged_df['spo2'].iloc[i] if pd.notna(merged_df['spo2'].iloc[i]) else "-"
            df2.loc[i + 1, 'H'] = merged_df['urine'].iloc[i] if pd.notna(merged_df['urine'].iloc[i]) else "-"
            df2.loc[i + 1, 'I'] = merged_df['mews'].iloc[i] if pd.notna(merged_df['mews'].iloc[i]) else "-"
            df2.loc[i + 1, 'J'] = '-'  # Placeholder for CVP
            df2.loc[i + 1, 'K'] = merged_df['text'].iloc[i] if pd.notna(merged_df['text'].iloc[i]) else "-"
            df2.loc[i + 1, 'L'] = merged_df['auditor_name'].iloc[i] if pd.notna(merged_df['auditor_name'].iloc[i]) else "-"
        
        # Merge patient data and vital signs into one DataFrame
        report_df = pd.concat([df1, df2], ignore_index=True)

        # print(report_df)
        filepath = f"temp/{patient_id}_{patient_df['fullname'].iloc[0].replace(' ', '_')}_report.xlsx"
        report_df.to_excel(filepath, index=False)

        decorator: ExcelDecorator = ExcelDecorator(filepath)
        decorator.decorate()

        if not os.path.exists(filepath):
            return {"error": "File not found"}
        
        # Open the file and stream it using a context manager
        def iter_file():
            with open(filepath, mode="rb") as file:
                yield from file
        
        # Add delete task to background after streaming completes
        background_tasks.add_task(delete_file, filepath)
        
        # Return the file as a streaming response
        return StreamingResponse(iter_file(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={os.path.basename(filepath)}"})
  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_report_excel_all")
def get_report_excel_all(request: PatientIDRequest, background_tasks: BackgroundTasks): # ✅
    db = get_firestore_db()
    file_path = generate_patient_report(request.patient_ids, db)

    wb = load_workbook(file_path)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    # Apply borders to all sheets
    for sheet_name in wb.sheetnames:
        
        ws = wb[sheet_name]
        ws.delete_rows(1)

        # Find the last row with content
        last_row = ws.max_row  # This will get the last row with any content

        # Apply borders from row 8 onwards (A8 to L) for all rows with content
        for row in range(7, last_row + 1):  # Start from row 8
            for col in range(1, 13):  # Columns A (1) to L (12)
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border

    # Save the workbook after applying the decoration
    wb.save(file_path)

    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    # Open the file and stream it using a context manager
    def iter_file():
        with open(file_path, mode="rb") as file:
            yield from file
    
    # Add delete task to background after streaming completes
    background_tasks.add_task(delete_file, file_path)

    return StreamingResponse(iter_file(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={os.path.basename(file_path)}"})
    # return FileResponse(file_path, filename="patient_report.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    # try:
    #     all_data = []
    #     for patient in patients:
    #     # Fetch patient data
    #         patient_ref = db.collection('patients').document(patient_id).get()
    #         if not patient_ref.exists:
    #             continue
    #         patient_data = patient_ref.to_dict()
    #         patient_data['patient_id'] = patient_id

    #         # Fetch MEWS data 
    #         mews_ref = db.collection('MEWS').where("patient_id", "==", patient_id)
    #         mews_docs = mews_ref.stream()
    #         mews_data = [doc.to_dict() for doc in mews_docs]

    #         # Combine into a DataFrame
    #         patient_df = pd.DataFrame([patient_data])
    #         mews_df = pd.DataFrame(mews_data)

    #         # Merge data
    #         report_df = pd.concat([patient_df, mews_df], ignore_index=True)

    #         # Convert to Excel file in memory
    #         output = io.BytesIO()
    #         with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    #             report_df.to_excel(writer, index=False, sheet_name="Report")

    #         output.seek(0)

    #     return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #                              headers={"Content-Disposition": "attachment; filename=patient_report.xlsx"})
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))