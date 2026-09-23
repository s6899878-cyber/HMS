import io
import base64
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.medical_report import MedicalReport
from app.models.test_result import TestResult
from app.services.openai_service import client
from app.core.config import settings

router = APIRouter()

def parse_value(val_str: str) -> float:
    try:
        # Extract first contiguous number from string
        import re
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", str(val_str).replace(',', ''))
        if matches:
            return float(matches[0])
    except:
        pass
    return None

def generate_trend_chart(df: pd.DataFrame, metric_name: str, color: str = '#3b82f6') -> str:
    if df.empty:
        return ""
    
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor('#1E293B')
    ax.set_facecolor('#1E293B')
    
    # Sort by date
    df = df.sort_values(by='date')
    
    ax.plot(df['date'], df['value'], color=color, linewidth=3, marker='o')
    ax.fill_between(df['date'], df['value'], alpha=0.3, color=color)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#475569')
    ax.spines['bottom'].set_color('#475569')
    ax.tick_params(colors='#94a3b8')
    ax.set_title(f"{metric_name} Trend", color='#F8FAFC', pad=10)
    
    # Optional: Format X axis for dates
    fig.autofmt_xdate()
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True, dpi=100)
    plt.close(fig)
    
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"

def get_ai_insights(metrics: Dict[str, Any]) -> Dict[str, Any]:
    if not metrics:
        return {
            "score": 0,
            "insights": ["No data available to generate insights."],
            "recommendations": ["Please upload a medical report to get started."]
        }
        
    prompt = f"""
    You are an expert health data analyst. Review the following recent metrics for a user:
    {json.dumps(metrics)}
    
    Based ONLY on this data, provide:
    1. An 'overall_score' from 0 to 100 representing general health progress (100 is perfectly normal/optimal).
    2. A list of 3 short 'insights' explaining what the data means. Do NOT diagnose diseases. Just explain the trends.
    3. A list of 3 'recommendations' for lifestyle or follow-ups.
    
    Return strict JSON: {{"overall_score": 85, "insights": [], "recommendations": []}}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        return json.loads(content)
    except Exception as e:
        print("AI Error:", e)
        return {
            "score": 0,
            "insights": ["AI analysis failed."],
            "recommendations": []
        }

def normalize_test_name(name: str) -> str:
    n = name.lower().strip()
    if n in ['hb', 'haemoglobin', 'hemoglobin (hb)', 'hgb']:
        return 'hemoglobin'
    if n in ['fasting blood sugar', 'fbs', 'glucose fasting', 'glucose (fasting)', 'fasting glucose']:
        return 'fasting glucose'
    if n in ['bp', 'blood pressure']:
        return 'blood pressure'
    if n in ['wbc', 'white blood cell', 'leukocyte count', 'white blood cells']:
        return 'wbc count'
    if n in ['rbc', 'red blood cell', 'erythrocyte count', 'red blood cells']:
        return 'rbc count'
    if n in ['plt', 'platelet', 'platelets']:
        return 'platelet count'
    if n in ['hba1c', 'glycosylated hemoglobin']:
        return 'hba1c'
    return n

@router.get("/dashboard")
def get_analytics_dashboard(
    time_range: str = "6M",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Calculate cutoff date
    now = datetime.utcnow()
    if time_range == "1M":
        cutoff = now - timedelta(days=30)
    elif time_range == "3M":
        cutoff = now - timedelta(days=90)
    elif time_range == "6M":
        cutoff = now - timedelta(days=180)
    elif time_range == "1Y":
        cutoff = now - timedelta(days=365)
    else:
        cutoff = now - timedelta(days=180)
        
    reports = db.query(MedicalReport).filter(
        MedicalReport.user_id == current_user.id,
        MedicalReport.uploaded_at >= cutoff
    ).all()
    
    report_ids = [r.id for r in reports]
    
    results = db.query(TestResult).filter(TestResult.report_id.in_(report_ids)).all()
    
    # Organize data by test name
    data_map = {}
    for r in results:
        report = next((rep for rep in reports if rep.id == r.report_id), None)
        if not report:
            continue
        
        raw_name = r.test_name.lower().strip()
        norm_name = normalize_test_name(raw_name)
        val = parse_value(r.value)
        if val is not None:
            if norm_name not in data_map:
                # Format display name nicely based on normalized key
                display_name = norm_name.title()
                if norm_name == 'hemoglobin': display_name = 'Hemoglobin'
                if norm_name == 'hba1c': display_name = 'HbA1c'
                if norm_name == 'wbc count': display_name = 'WBC Count'
                if norm_name == 'rbc count': display_name = 'RBC Count'
                
                data_map[norm_name] = {"name": display_name, "unit": r.unit, "history": []}
            data_map[norm_name]["history"].append({
                "date": report.uploaded_at,
                "value": val
            })
            
    # Generate cards and charts
    cards = []
    charts = []
    current_metrics_for_ai = {}
    
    # Priority metrics to look for
    priority_names = ['heart rate', 'blood pressure', 'weight', 'sleep', 'hemoglobin', 'fasting glucose', 'platelet']
    
    for key, item in data_map.items():
        history = sorted(item["history"], key=lambda x: x["date"])
        current_val = history[-1]["value"]
        prev_val = history[-2]["value"] if len(history) > 1 else current_val
        
        change = current_val - prev_val
        trend = "Stable"
        if change > 0:
            trend = "Increased"
        elif change < 0:
            trend = "Decreased"
            
        current_metrics_for_ai[item["name"]] = current_val
        
        # Build Card (for all priority metrics or any metrics found)
        cards.append({
            "name": item["name"],
            "current": current_val,
            "unit": item["unit"] or "",
            "change": round(change, 2),
            "trend": trend
        })
        
        # Build Matplotlib Chart
        df = pd.DataFrame(history)
        chart_b64 = generate_trend_chart(df, item["name"])
        charts.append({
            "name": item["name"],
            "current": current_val,
            "unit": item["unit"] or "",
            "trend": trend,
            "image_base64": chart_b64
        })
        
    ai_insights = get_ai_insights(current_metrics_for_ai)
    
    # Fetch recent reports for linking
    recent_reports = db.query(MedicalReport).filter(MedicalReport.user_id == current_user.id).order_by(MedicalReport.uploaded_at.desc()).limit(3).all()
    recent_reports_data = [{
        "id": r.id,
        "title": r.title or r.original_filename,
        "date": r.uploaded_at.strftime("%Y-%m-%d")
    } for r in recent_reports]

    return {
        "cards": cards,
        "charts": charts,
        "overall_score": ai_insights.get("overall_score", 0),
        "insights": ai_insights.get("insights", []),
        "recommendations": ai_insights.get("recommendations", []),
        "recent_reports": recent_reports_data
    }
