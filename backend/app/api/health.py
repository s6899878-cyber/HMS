from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.health_metric import HealthMetric
from app.models.medical_report import MedicalReport
from app.schemas.health import HealthMetricCreate, HealthMetricOut
from app.models.test_result import TestResult
from app.models.hospital import Hospital, HospitalSpecialty
from app.services.openai_service import client
import json

router = APIRouter()

@router.get("/metrics", response_model=List[HealthMetricOut])
def get_all_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(HealthMetric).filter(HealthMetric.user_id == current_user.id).order_by(HealthMetric.recorded_at.desc()).all()

@router.post("/metrics", response_model=HealthMetricOut)
def create_metric(
    metric_in: HealthMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    metric = HealthMetric(user_id=current_user.id, **metric_in.dict())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric

@router.get("/metrics/{metric_type}", response_model=List[HealthMetricOut])
def get_metric_history(
    metric_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    metrics = db.query(HealthMetric).filter(
        HealthMetric.user_id == current_user.id,
        HealthMetric.metric_type == metric_type
    ).order_by(HealthMetric.recorded_at.asc()).all()
    return metrics

@router.get("/dashboard/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_reports = db.query(MedicalReport).filter(MedicalReport.user_id == current_user.id).count()
    analyses_completed = db.query(MedicalReport).filter(
        MedicalReport.user_id == current_user.id,
        MedicalReport.analysis_status == "completed"
    ).count()
    
    recent_reports = db.query(MedicalReport).filter(
        MedicalReport.user_id == current_user.id
    ).order_by(MedicalReport.uploaded_at.desc()).limit(3).all()
    
    return {
        "totalReports": total_reports,
        "analyses": analyses_completed,
        "healthScore": 85, # Mocked health score for now
        "recentReports": [
            {
                "id": str(r.id),
                "title": r.title,
                "date": r.uploaded_at.strftime("%Y-%m-%d"),
                "status": r.analysis_status
            }
            for r in recent_reports
        ]
    }

@router.get("/recommendations")
def get_health_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch recent medical reports
    recent_reports = db.query(MedicalReport).filter(MedicalReport.user_id == current_user.id).order_by(MedicalReport.uploaded_at.desc()).limit(5).all()
    
    if not recent_reports:
        # Fallback if no reports
        return {
            "insights": [
                {"title": "General Wellness", "description": "Maintain a balanced diet rich in fruits, vegetables, and whole grains.", "icon": "Nutrition"},
                {"title": "Stay Active", "description": "Aim for at least 30 minutes of moderate physical activity most days of the week.", "icon": "Activity"},
                {"title": "Restful Sleep", "description": "Ensure 7-9 hours of quality sleep per night for optimal recovery.", "icon": "Sleep"},
                {"title": "Hydration", "description": "Drink adequate water daily to maintain energy levels and bodily functions.", "icon": "Hydration"}
            ],
            "hospitals": [],
            "specialties_identified": []
        }

    report_ids = [r.id for r in recent_reports]
    results = db.query(TestResult).filter(TestResult.report_id.in_(report_ids)).all()
    
    abnormal_results = [r for r in results if r.status and r.status.lower() != 'normal']
    
    # If no abnormal results, take up to 10 normal ones to feed AI
    if not abnormal_results:
        metrics_data = [{"test": r.test_name, "value": r.value, "status": r.status} for r in results[:10]]
    else:
        metrics_data = [{"test": r.test_name, "value": r.value, "status": r.status} for r in abnormal_results]

    prompt = f"""
    The user has the following test results:
    {json.dumps(metrics_data)}
    
    Based ONLY on these metrics, provide a detailed medical analysis in strict JSON format:
    1. "disease_analysis": A paragraph explaining what the abnormal metrics mean (what is high/low) and what diseases or conditions they might indicate.
    2. "insights": A list of 4 highly specific lifestyle and nutrition recommendations. YOU MUST INCLUDE EXACT QUANTITIES AND AMOUNTS based on the test values (e.g., instead of "Drink water", say "Drink 3.5 liters of water daily to flush excess glucose"; instead of "Eat iron rich food", say "Consume 2 cups of cooked spinach or 100g of lentils daily to increase hemoglobin"). Tell the user exactly *how much* of what to take.
    3. "specialties_identified": A list of 1 to 3 medical specialties the user might need to consult.
    
    Strict JSON format:
    {{
      "disease_analysis": "Your recent report shows low Hemoglobin (Anemia risk) and low Platelet count, which could indicate a viral infection such as Dengue.",
      "insights": [
        {{"title": "Nutrition", "description": "Consume exactly 2 cups of iron-rich leafy greens (like spinach) and 150g of lean protein daily to combat low hemoglobin.", "icon": "Nutrition"}},
        {{"title": "Hydration", "description": "Drink at least 3 to 4 liters of water every day to support blood circulation.", "icon": "Hydration"}}
      ],
      "specialties_identified": ["Hematology", "General Medicine"]
    }}
    The 'icon' field must be one of: Nutrition, Hydration, Sleep, Activity, Medical.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        ai_data = json.loads(response.choices[0].message.content)
    except Exception as e:
        ai_data = {
            "disease_analysis": "Could not analyze the report at this time.",
            "insights": [
                {"title": "Error generating insights", "description": str(e), "icon": "Medical"}
            ],
            "specialties_identified": ["General Medicine"]
        }

    specialties = ai_data.get("specialties_identified", ["General Medicine"])
    
    # Query database for matching hospitals based on specialties
    recommended_hospitals = []
    
    for spec in specialties:
        search_term = f"%{spec}%"
        hospitals = db.query(Hospital).join(HospitalSpecialty).filter(
            HospitalSpecialty.specialty_name.ilike(search_term)
        ).limit(2).all()
        
        for h in hospitals:
            if not any(rh['id'] == h.id for rh in recommended_hospitals):
                recommended_hospitals.append({
                    "id": h.id,
                    "name": h.name,
                    "type": h.hospital_type,
                    "government_or_private": h.government_or_private,
                    "phone": h.phone,
                    "city": h.location.city if h.location else "Unknown",
                    "matched_specialty": spec
                })
    
    # If no hospitals matched by specialty, just grab top 3 hospitals as general recommendation
    if not recommended_hospitals:
        top_hospitals = db.query(Hospital).limit(3).all()
        for h in top_hospitals:
            recommended_hospitals.append({
                "id": h.id,
                "name": h.name,
                "type": h.hospital_type,
                "government_or_private": h.government_or_private,
                "phone": h.phone,
                "city": h.location.city if h.location else "Unknown",
                "matched_specialty": "General Medicine"
            })
            
    ai_data["hospitals"] = recommended_hospitals
    return ai_data


