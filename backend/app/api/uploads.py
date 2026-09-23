from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.medical_report import MedicalReport
from app.schemas.reports import MedicalReportOut
from app.services.openai_service import analyze_medical_report_image
from app.models.test_result import TestResult
import json
import base64
import os
import shutil
import uuid

router = APIRouter()

@router.post("/", response_model=MedicalReportOut)
async def upload_medical_report(
    file: UploadFile = File(...),
    title: str = "Untitled Report",
    report_type: str = "General",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Read contents and encode to base64 for OpenAI
    contents = await file.read()
    b64_str = base64.b64encode(contents).decode("utf-8")
    content_type = file.content_type
    base64_image_data = f"data:{content_type};base64,{b64_str}"
    
    # Save locally to static folder for history
    static_dir = os.path.join(os.getcwd(), "app", "static", "uploads")
    os.makedirs(static_dir, exist_ok=True)
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(static_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(contents)
        
    local_url = f"http://localhost:8000/static/uploads/{unique_filename}"
    
    # Save metadata to DB
    new_report = MedicalReport(
        user_id=current_user.id,
        title=title,
        original_filename=file.filename,
        file_type=file.content_type,
        cloudinary_public_id=unique_filename,
        cloudinary_url=local_url,
        file_size=len(contents),
        report_type=report_type,
        analysis_status="pending"
    )
    
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    # Trigger AI analysis immediately
    try:
        ai_data = analyze_medical_report_image(base64_image_data)
        new_report.analysis_status = "completed"
        new_report.ai_summary = json.dumps({
            "disease_prediction": ai_data.get("disease_prediction", "Unknown"),
            "summary": ai_data.get("summary", "")
        })
        
        abnormal_metrics = ai_data.get("abnormal_metrics", [])
        for metric in abnormal_metrics:
            tr = TestResult(
                report_id=new_report.id,
                test_name=metric.get("test_name"),
                value=metric.get("value"),
                unit=metric.get("unit"),
                reference_range=metric.get("reference_range"),
                status=metric.get("status")
            )
            db.add(tr)
            
        db.commit()
        db.refresh(new_report)
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        new_report.analysis_status = "failed"
        db.commit()
        db.refresh(new_report)
    
    return new_report
