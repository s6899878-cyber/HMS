from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class HealthProfile(Base):
    __tablename__ = "health_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Float, nullable=True) # in cm
    weight = Column(Float, nullable=True) # in kg
    blood_group = Column(String, nullable=True)
    allergies = Column(Text, nullable=True)
    existing_conditions = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    emergency_contact = Column(String, nullable=True)
    
    user = relationship("User", back_populates="profile")
