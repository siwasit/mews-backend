from pydantic import BaseModel, Field
from datetime import datetime

class PatientData(BaseModel):
    age: str
    bed_number: str
    color_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    fullname: str
    gender: str
    hospital_number: str
    patient_id: str
    ward: str

class PatientUserLinks(BaseModel):
    patient_id: str
    uid: str