from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TestResultOut(BaseModel):
    id: int
    test_name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class MedicalReportBase(BaseModel):
    title: str
    report_type: Optional[str] = None

class MedicalReportCreate(MedicalReportBase):
    pass

class MedicalReportOut(MedicalReportBase):
    id: int
    user_id: int
    original_filename: str
    file_type: str
    cloudinary_url: str
    file_size: int
    analysis_status: str
    ai_summary: Optional[str] = None
    uploaded_at: datetime
    test_results: List[TestResultOut] = []

    class Config:
        from_attributes = True

class ReportComparison(BaseModel):
    metric: str
    previous: float
    current: float
    change: float
    trend: str
