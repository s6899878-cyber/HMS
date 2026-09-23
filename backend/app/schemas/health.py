from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HealthMetricCreate(BaseModel):
    metric_type: str
    value: float
    unit: str

class HealthMetricOut(HealthMetricCreate):
    id: int
    user_id: int
    recorded_at: datetime

    class Config:
        from_attributes = True

class HealthTrend(BaseModel):
    metric: str
    latest: float
    previous: float
    change: float
    trend: str
