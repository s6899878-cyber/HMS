from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class HealthMetric(Base):
    __tablename__ = "health_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    metric_type = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="metrics")
