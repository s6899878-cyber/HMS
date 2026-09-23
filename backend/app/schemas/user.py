from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class HealthProfileBase(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    existing_conditions: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact: Optional[str] = None

class HealthProfileUpdate(HealthProfileBase):
    pass

class HealthProfileOut(HealthProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
