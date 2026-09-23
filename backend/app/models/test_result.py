from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("medical_reports.id"), nullable=False)
    
    test_name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    reference_range = Column(String, nullable=True)
    status = Column(String, nullable=True)
    
    report = relationship("MedicalReport", back_populates="test_results")
