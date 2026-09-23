from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class HospitalLocationBase(BaseModel):
    address: str
    city: str
    district: str
    state: str
    union_territory: bool
    pincode: str
    latitude: float
    longitude: float
    google_maps_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class HospitalVerificationBase(BaseModel):
    verified: bool
    verification_status: str
    accreditation_name: str
    certificate_number: Optional[str] = None
    validity: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    last_verified: datetime
    
    class Config:
        from_attributes = True

class HospitalSpecialtyBase(BaseModel):
    specialty_name: str
    class Config:
        from_attributes = True

class HospitalFacilityBase(BaseModel):
    facility_name: str
    class Config:
        from_attributes = True

class TreatmentCostBase(BaseModel):
    disease: str
    treatment: str
    procedure: Optional[str] = None
    cost_min: Optional[float] = None
    cost_max: Optional[float] = None
    currency: str
    cost_type: str
    package_type: Optional[str] = None
    room_category: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    last_verified: datetime
    class Config:
        from_attributes = True

class PatientStatisticBase(BaseModel):
    metric_type: str
    disease: Optional[str] = None
    volume: int
    period: str
    source: str
    source_url: Optional[str] = None
    last_verified: datetime
    class Config:
        from_attributes = True

class HospitalBase(BaseModel):
    name: str
    external_id: str
    hospital_group: Optional[str] = None
    hospital_type: str
    government_or_private: str
    phone: Optional[str] = None
    emergency_phone: Optional[str] = None
    email: Optional[str] = None
    official_website: Optional[str] = None

class HospitalCreate(HospitalBase):
    pass

class HospitalOut(HospitalBase):
    id: int
    location: Optional[HospitalLocationBase] = None
    verifications: List[HospitalVerificationBase] = []
    specialties: List[HospitalSpecialtyBase] = []
    facilities: List[HospitalFacilityBase] = []
    costs: List[TreatmentCostBase] = []
    patient_stats: List[PatientStatisticBase] = []
    
    # Computed fields at query time
    match_score: Optional[int] = None
    why_recommended: Optional[List[str]] = []
    distance_km: Optional[float] = None
    best_for: Optional[str] = None
    
    class Config:
        from_attributes = True

class SavedHospitalCreate(BaseModel):
    external_id: str
    name: str
    city: str
    specialties: List[str] = []

class SavedHospitalOut(SavedHospitalCreate):
    id: int
    user_id: int
    saved_at: datetime
    
    class Config:
        from_attributes = True
