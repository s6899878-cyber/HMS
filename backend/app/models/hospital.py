from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Hospital(Base):
    __tablename__ = "hospitals"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    hospital_group = Column(String, nullable=True)
    hospital_type = Column(String) # Multi-specialty, Super-specialty, Specialty, General
    government_or_private = Column(String)
    
    # Contact
    phone = Column(String, nullable=True)
    emergency_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    official_website = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    location = relationship("HospitalLocation", back_populates="hospital", uselist=False, cascade="all, delete-orphan")
    verifications = relationship("HospitalVerification", back_populates="hospital", cascade="all, delete-orphan")
    specialties = relationship("HospitalSpecialty", back_populates="hospital", cascade="all, delete-orphan")
    facilities = relationship("HospitalFacility", back_populates="hospital", cascade="all, delete-orphan")
    costs = relationship("TreatmentCost", back_populates="hospital", cascade="all, delete-orphan")
    patient_stats = relationship("PatientStatistic", back_populates="hospital", cascade="all, delete-orphan")

class HospitalLocation(Base):
    __tablename__ = "hospital_locations"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    
    address = Column(String)
    city = Column(String, index=True)
    district = Column(String, index=True)
    state = Column(String, index=True)
    union_territory = Column(Boolean, default=False)
    pincode = Column(String, index=True)
    
    latitude = Column(Float)
    longitude = Column(Float)
    google_maps_url = Column(String, nullable=True)

    hospital = relationship("Hospital", back_populates="location")

class HospitalVerification(Base):
    __tablename__ = "hospital_verifications"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    
    verified = Column(Boolean, default=False)
    verification_status = Column(String) # Active, Pending, Expired
    accreditation_name = Column(String) # NABH, JCI, NABL
    certificate_number = Column(String, nullable=True)
    validity = Column(String, nullable=True) # Valid till date string
    source = Column(String)
    source_url = Column(String, nullable=True)
    last_verified = Column(DateTime)

    hospital = relationship("Hospital", back_populates="verifications")

class HospitalSpecialty(Base):
    __tablename__ = "hospital_specialties"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    specialty_name = Column(String, index=True) # Standardized (e.g. Cardiology)
    
    hospital = relationship("Hospital", back_populates="specialties")

class HospitalFacility(Base):
    __tablename__ = "hospital_facilities"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    facility_name = Column(String, index=True) # ICU, 24x7_Emergency, PET_CT
    
    hospital = relationship("Hospital", back_populates="facilities")

class TreatmentCost(Base):
    __tablename__ = "treatment_costs"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    
    disease = Column(String, index=True)
    treatment = Column(String, index=True)
    procedure = Column(String, nullable=True)
    
    cost_min = Column(Float, nullable=True)
    cost_max = Column(Float, nullable=True)
    currency = Column(String, default="INR")
    cost_type = Column(String) # Government package rate, Estimated market range, Insurance package
    package_type = Column(String, nullable=True)
    room_category = Column(String, nullable=True)
    
    source = Column(String)
    source_url = Column(String, nullable=True)
    last_verified = Column(DateTime)

    hospital = relationship("Hospital", back_populates="costs")

class PatientStatistic(Base):
    __tablename__ = "patient_statistics"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    
    metric_type = Column(String) # annual_patient_volume, annual_surgeries, disease_specific
    disease = Column(String, nullable=True)
    volume = Column(Integer)
    period = Column(String) # FY2025, 2024
    
    source = Column(String)
    source_url = Column(String, nullable=True)
    last_verified = Column(DateTime)

    hospital = relationship("Hospital", back_populates="patient_stats")
