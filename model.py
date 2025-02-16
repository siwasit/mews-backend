from pydantic import BaseModel, Field # type: ignore
from datetime import datetime
from typing import Optional, List

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
    mews: str

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

class PatientIDRequest(BaseModel):
    patient_ids: List[str]  # Expecting a list of patient_id values


class UserAuth(BaseModel):
    uid: str  # Firebase UID
    password: str  # Plaintext password

class CustomToken(BaseModel):
    id_token: str  # Plaintext password