from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    profile = relationship("HealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reports = relationship("MedicalReport", back_populates="user", cascade="all, delete-orphan")
    metrics = relationship("HealthMetric", back_populates="user", cascade="all, delete-orphan")
    saved_hospitals = relationship("SavedHospital", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
