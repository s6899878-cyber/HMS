from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class MedicalReport(Base):
    __tablename__ = "medical_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    cloudinary_public_id = Column(String, nullable=False)
    cloudinary_url = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    report_type = Column(String, nullable=True) 
    analysis_status = Column(String, default="pending") 
    ai_summary = Column(Text, nullable=True)
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="reports")
    test_results = relationship("TestResult", back_populates="report", cascade="all, delete-orphan")
