from fastapi import HTTPException 
from firebase_db import get_firestore_db
import pandas as pd # type: ignore
import uuid

def strip_timezone(df):
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.tz_localize(None)  # Remove timezone info
    return df

def generate_patient_report(patient_ids, db):
    """
    Generate an Excel report for multiple patients, storing each patient's data in a separate sheet.
    
    Args:
        patient_ids (list): List of patient IDs to retrieve and process.
    
    Returns:
        str: File path of the generated Excel report.
    """
    if not patient_ids:
        raise HTTPException(status_code=400, detail="No patient IDs provided")

    unique_id = uuid.uuid4().hex
    file_path = f"temp/{unique_id}_patients_fullreport.xlsx"

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        for patient_id in patient_ids:
            patient_ref = db.collection('patients').document(patient_id).get()
            if not patient_ref.exists:
                continue  # Skip if patient not found
            
            patient_data = patient_ref.to_dict()
            patient_data['patient_id'] = patient_id

            # Fetch MEWS data 
            mews_ref = db.collection('mews').where("patient_id", "==", patient_id)
            mews_docs = mews_ref.stream()
            mews_data = [{"mews_id": doc.id, **doc.to_dict()} for doc in mews_docs]

            note_ref = db.collection('inspection_notes').where("patient_id", "==", patient_id)
            note_docs = note_ref.stream()
            note_data = [doc.to_dict() for doc in note_docs]

            # Convert Firestore data to DataFrames
            patient_df = pd.DataFrame([patient_data])
            mews_df = pd.DataFrame(mews_data)
            note_df = pd.DataFrame(note_data)

            # Process timezones
            patient_df = strip_timezone(patient_df)
            mews_df = strip_timezone(mews_df)
            note_df = strip_timezone(note_df)

            # Map auditor names from 'users' collection
            auditor_dict = {}
            for user_id in note_df["audit_by"].unique().tolist():
                user_ref = db.collection("users").document(user_id).get()
                if user_ref.exists:
                    auditor_dict[user_id] = user_ref.to_dict().get("fullname", "Unknown")

            note_df["auditor_name"] = note_df["audit_by"].map(auditor_dict)

            # Create patient details DataFrame
            df1 = pd.DataFrame(columns=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'])
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

            # Create vital signs DataFrame
            df2 = pd.DataFrame(columns=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'])
            df2.loc[0] = ['วันเวลา', 'C', 'T', 'P', 'R', 'BP', 'O2 Sat', 'Urine', 'Total Score (MEWs)', 'CVP', 'หมายเหตุ', 'แก้ไขโดย']

            # Merge MEWS and Notes data
            merged_df = pd.merge(mews_df, note_df, on="mews_id", how="inner").sort_values(by='time', ascending=True)

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

            # Combine patient details and vital signs
            report_df = pd.concat([df1, df2], ignore_index=True)

            report_df.to_excel(writer, sheet_name=f"Patient_{patient_id}", index=False)
            
    return file_path