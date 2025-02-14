from pydantic import BaseModel, Field # type: ignore
from datetime import datetime

class PatientData(BaseModel):
    age: str
    bed_number: str
    fullname: str
    gender: str
    hospital_number: str
    ward: str

class PatientUserLinks(BaseModel):
    patient_id: str
    user_id: str

class Users(BaseModel):
    nurse_id: str
    password: str 
    role: str
    fullname: str

class MEWS(BaseModel):
    patient_id: str
    consciousness: str
    heart_rate: str
    urine: str
    spo2: str
    temperature: str
    respiratory_rate: str
    blood_pressure: str

class Token(BaseModel):
    access_token: str
    token_type: str

class InspectionsNote(BaseModel):
    text: str
    mews_id: str
    patient_id: str
    audit_by: str
    time: datetime

class NoteRequest(BaseModel):
    text: str
    audit_by: str
