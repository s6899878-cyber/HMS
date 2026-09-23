from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.medical_report import MedicalReport
from app.schemas.reports import MedicalReportOut
from app.services.cloudinary_service import delete_file

router = APIRouter()

@router.get("/", response_model=List[MedicalReportOut])
def get_user_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reports = db.query(MedicalReport).filter(MedicalReport.user_id == current_user.id).all()
    return reports

@router.get("/{report_id}", response_model=MedicalReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id, MedicalReport.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id, MedicalReport.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Delete from Cloudinary
    resource_type = "image" if report.file_type.startswith("image") else "raw"
    delete_file(report.cloudinary_public_id, resource_type)
    
    # Delete from DB
    db.delete(report)
    db.commit()
    
    return {"success": True, "message": "Report deleted successfully"}
