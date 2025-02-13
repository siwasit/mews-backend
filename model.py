from pydantic import BaseModel, Field # type: ignore
from datetime import datetime

class PatientData(BaseModel):
    age: str
    bed_number: str
    color_key: str
    created_at: datetime = Field(default_factory=datetime)
    fullname: str
    gender: str
    hospital_number: str
    patient_id: str
    ward: str

class PatientUserLinks(BaseModel):
    patient_id: str
    uid: str

class Users(BaseModel):
    nurse_id: str
    email: str
    role: str
    fullname: str
    ...

class MEWS(BaseModel):
    mews_id: str
    consciousness: str
    heart_rate: str
    urine: str
    spo2: str
    created_at: datetime = Field(default_factory=datetime)
    ...

class Token(BaseModel):
    access_token: str
    token_type: str

