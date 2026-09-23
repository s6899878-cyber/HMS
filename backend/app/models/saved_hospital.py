from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SavedHospital(Base):
    __tablename__ = "saved_hospitals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    external_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    saved_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="saved_hospitals")
