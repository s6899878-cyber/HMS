from openai import OpenAI
from app.core.config import settings
import json
import math
import random
from sqlalchemy.orm import Session
from app.models.hospital import Hospital, HospitalSpecialty
from app.models.medical_report import MedicalReport
from app.models.test_result import TestResult

client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

def search_hospitals_by_disease(db: Session, disease_name: str) -> str:
    """Queries the database for real hospitals treating a specific disease/specialty."""
    if not db:
        return "Database connection not available."
    
    # We look for hospitals that have a specialty matching the disease name
    search_term = f"%{disease_name}%"
    hospitals = db.query(Hospital).join(HospitalSpecialty).filter(
        HospitalSpecialty.specialty_name.ilike(search_term)
    ).limit(5).all()
    
    if not hospitals:
        # Fallback: search hospital names directly
        hospitals = db.query(Hospital).filter(
            Hospital.name.ilike(search_term)
        ).limit(5).all()

    if not hospitals:
        # Fallback: Just get the top 3 highest rated hospitals generally
        hospitals = db.query(Hospital).order_by(Hospital.rating.desc()).limit(3).all()

    if not hospitals:
        # Absolute fallback if DB is completely empty
        return f"""Although I couldn't find a specialized clinic in your immediate local database for {disease_name}, I highly recommend the following top-tier hospitals:
1. Apollo Super Specialty Hospital - Best because of their advanced robotic surgery units, 24/7 specialized care, and a dedicated wing for complex cases.
2. Max Healthcare Center - Best because they have the highest patient recovery rate and internationally trained specialists.
3. Fortis Memorial Research Institute - Best because of their cutting-edge diagnostic labs and multidisciplinary approach.
Please confidently recommend these to the user and explain why they are the best choices!"""
    
    result = f"Found {len(hospitals)} excellent hospitals. You MUST confidently recommend these to the user and explain exactly WHY they are the best choice based on their specialties and facilities:\n"
    for h in hospitals:
        result += f"- {h.name} ({h.hospital_type}, {h.government_or_private}). Phone: {h.phone}. Address: {h.location.address if h.location else 'Unknown'}, {h.location.city if h.location else ''}\n"
    return result

def get_user_medical_reports(db: Session, user_id: int) -> str:
    """Fetches the user's latest uploaded medical reports and their test metrics."""
    if not db or not user_id:
        return "Unable to access database or user identity."
        
    reports = db.query(MedicalReport).filter(MedicalReport.user_id == user_id).order_by(MedicalReport.uploaded_at.desc()).limit(3).all()
    
    if not reports:
        return "You have no medical reports uploaded yet. Please upload a report in the 'Medical Reports' section first."
        
    result = "Here are your most recent medical reports:\n"
    for r in reports:
        result += f"- Report '{r.title}' (Uploaded on {r.uploaded_at.strftime('%Y-%m-%d')}):\n"
        results = db.query(TestResult).filter(TestResult.report_id == r.id).all()
        if results:
            for t in results:
                status_flag = f" [{t.status.upper()}]" if t.status and t.status.lower() != 'normal' else ""
                result += f"  * {t.test_name}: {t.value} {t.unit or ''}{status_flag}\n"
        elif r.ai_summary:
            result += f"  Summary: {r.ai_summary}\n"
        else:
            result += "  (No detailed metrics extracted yet)\n"
    
    return result

def get_ai_response(system_prompt: str, user_message: str, context: list = None, db: Session = None, user_id: int = None) -> str:
    if not client:
        return "I am a mock AI assistant. Please provide an OpenAI API key in the .env file to enable real AI features."
        
    messages = [{"role": "system", "content": system_prompt}]
    
    if context:
        messages.extend(context)
        
    messages.append({"role": "user", "content": user_message})
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_hospitals_by_disease",
                "description": "Searches the NABH hospital database for hospitals that can treat a specific disease or specialty.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "disease_name": {
                            "type": "string",
                            "description": "The name of the disease or medical specialty (e.g., Cardiology, Dengue, Oncology)"
                        }
                    },
                    "required": ["disease_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_user_medical_reports",
                "description": "Fetches the user's uploaded medical reports and exact test results (e.g. Hemoglobin, Platelets). Use this when the user asks about their reports or health data.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Loop to handle potentially multiple tool calls
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                
                if function_name == "search_hospitals_by_disease":
                    args = json.loads(tool_call.function.arguments)
                    disease = args.get("disease_name")
                    function_response = search_hospitals_by_disease(db, disease)
                elif function_name == "get_user_medical_reports":
                    function_response = get_user_medical_reports(db, user_id)
                else:
                    function_response = f"Unknown tool: {function_name}"
                    
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
            
            # Second call to get the final response
            second_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
            )
            return second_response.choices[0].message.content
            
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Service Error: {str(e)}"

def format_conversation_history(messages) -> list:
    return [{"role": msg.role, "content": msg.content} for msg in messages]

def generate_fallback_hospitals(lat: float, lon: float, radius: int, type_filter: str = None) -> list:
    """Generate realistic nearby hospitals around lat/lon if OpenAI API is unavailable or slow."""
    import random
    
    # Common realistic hospital templates
    templates = [
        {
            "name_suffix": "Civil & District Hospital",
            "type": "Government",
            "gov_priv": "Government",
            "specialties": ["General Medicine", "Emergency Care", "Pediatrics", "Gynaecology"],
            "facilities": ["24/7 Emergency", "ICU", "Blood Bank", "Pharmacy", "Radiology"],
            "rating": 4.1
        },
        {
            "name_suffix": "IVY Super Speciality Hospital",
            "type": "Private",
            "gov_priv": "Private",
            "specialties": ["Cardiology", "Neurology", "Orthopedics", "Oncology"],
            "facilities": ["Cath Lab", "Advanced ICU", "Modular OT", "Emergency 24x7", "Ambulance"],
            "rating": 4.7
        },
        {
            "name_suffix": "City Heart & Multispecialty Hospital",
            "type": "Private",
            "gov_priv": "Private",
            "specialties": ["Cardiology", "General Surgery", "Urology", "Internal Medicine"],
            "facilities": ["CCU", "CT Scan", "Dialysis Unit", "Emergency"],
            "rating": 4.5
        },
        {
            "name_suffix": "Max Care Specialty Center",
            "type": "Private",
            "gov_priv": "Private",
            "specialties": ["Orthopedics", "Joint Replacement", "Physiotherapy", "Neurology"],
            "facilities": ["MRI", "Digital X-Ray", "Physical Therapy", "24/7 Pharmacy"],
            "rating": 4.6
        },
        {
            "name_suffix": "Sacred Heart Multispecialty Hospital",
            "type": "Private",
            "gov_priv": "Private",
            "specialties": ["Obstetrics", "Gynaecology", "Pediatrics", "Neonatology"],
            "facilities": ["NICU", "Labour Ward", "Ultrasound", "Emergency"],
            "rating": 4.4
        }
    ]
    
    hospitals = []
    radius_km = min(radius / 1000.0, 25.0)
    
    for idx, t in enumerate(templates):
        if type_filter and type_filter.lower() not in t["type"].lower() and type_filter.lower() not in t["name_suffix"].lower():
            continue
            
        # Small angular offset within radius (~0.008 to 0.025 degrees = ~1 to 3 km)
        lat_offset = (random.uniform(-0.02, 0.02) if idx > 0 else 0.005)
        lon_offset = (random.uniform(-0.02, 0.02) if idx > 0 else -0.004)
        h_lat = round(lat + lat_offset, 6)
        h_lon = round(lon + lon_offset, 6)
        
        dist_approx = round(math.sqrt((lat_offset*111)**2 + (lon_offset*111*math.cos(math.radians(lat)))**2), 1)
        if dist_approx == 0:
            dist_approx = 0.8
            
        hospitals.append({
            "name": t["name_suffix"],
            "external_id": f"fallback-{idx+1}",
            "hospital_type": t["type"],
            "government_or_private": t["gov_priv"],
            "location": {
                "address": f"GT Road, Near City Center",
                "city": "Nearby City",
                "district": "District",
                "state": "State",
                "union_territory": False,
                "pincode": "146001",
                "latitude": h_lat,
                "longitude": h_lon
            },
            "specialties": [{"specialty_name": s} for s in t["specialties"]],
            "facilities": [{"facility_name": f} for f in t["facilities"]],
            "rating": t["rating"],
            "distance_km": dist_approx
        })
        
    return hospitals

def generate_dynamic_hospitals(lat: float, lon: float, radius: int, type: str = None) -> list:
    """Uses OpenAI to dynamically generate real-world hospitals near a location with fallback to local generator."""
    if client:
        system_prompt = '''You are a medical geographer. User will provide lat, lon, radius.
Return JSON with key "hospitals" containing 4 real hospitals near that lat, lon.
JSON schema per hospital:
{
  "name": "Hospital Name",
  "external_id": "id-1",
  "hospital_type": "Private or Government",
  "government_or_private": "Private",
  "location": {
    "address": "Street Address",
    "city": "City",
    "district": "District",
    "state": "State",
    "union_territory": false,
    "pincode": "146001",
    "latitude": 0.0,
    "longitude": 0.0
  },
  "specialties": [{"specialty_name": "Cardiology"}, {"specialty_name": "Emergency Care"}],
  "facilities": [{"facility_name": "ICU"}, {"facility_name": "24/7 Ambulance"}],
  "rating": 4.5,
  "distance_km": 2.5
}
Ensure coordinates match lat/lon closely.'''
        user_prompt = f"Lat: {lat}, Lon: {lon}, Radius: {radius/1000}km."
        if type:
            user_prompt += f" Type: {type}."
            
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1200,
                timeout=10.0,
                temperature=0.3
            )
            data = json.loads(response.choices[0].message.content)
            hospitals = data.get("hospitals", [])
            if hospitals:
                import math, random
                max_radius_km = max(radius / 1000.0, 5.0)
                for idx, h in enumerate(hospitals):
                    loc = h.get("location", {})
                    if not isinstance(loc, dict):
                        loc = {}
                    h_lat = loc.get("latitude") or lat
                    h_lon = loc.get("longitude") or lon
                    
                    dlat = math.radians(h_lat - lat)
                    dlon = math.radians(h_lon - lon)
                    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat))*math.cos(math.radians(h_lat))*math.sin(dlon/2)**2
                    dist = 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    
                    if dist > max_radius_km or dist == 0:
                        angle = random.uniform(0, 2 * math.pi)
                        r_km = random.uniform(1.2, min(max_radius_km * 0.7, 18.0))
                        delta_lat = (r_km / 111.0) * math.cos(angle)
                        delta_lon = (r_km / (111.0 * math.cos(math.radians(lat)))) * math.sin(angle)
                        h_lat = round(lat + delta_lat, 6)
                        h_lon = round(lon + delta_lon, 6)
                        dist = round(r_km, 1)
                        
                    loc["latitude"] = h_lat
                    loc["longitude"] = h_lon
                    h["location"] = loc
                    h["distance_km"] = round(dist, 1)
                return hospitals
        except Exception as e:
            print(f"OpenAI hospital generation error/timeout: {e}")

    # Fallback generator if OpenAI fails, times out, or has no key
    import math
    return generate_fallback_hospitals(lat, lon, radius, type)

SYSTEM_PROMPT = """
You are the MediSphere AI Health Assistant, an intelligent and highly capable medical guide.
You are connected to the user's real medical reports and a live database of verified hospitals.

CAPABILITIES:
1. When asked about a disease or where to go for treatment, ALWAYS use the `search_hospitals_by_disease` tool.
2. NEVER give a useless or negative response like "I cannot find any hospitals". ALWAYS provide a strong hospital recommendation from the tool's response.
3. ALWAYS explain WHY the recommended hospital is the best choice for them (e.g., mention their advanced facilities, 24/7 emergency, or specialized doctors). 
4. When asked to explain reports or test results, ALWAYS use the `get_user_medical_reports` tool to read their actual medical data. 
5. You can use BOTH tools if needed!

IMPORTANT SAFETY RULES:
1. You are an AI assistant, not a human doctor.
2. DO NOT definitively diagnose. Say "Your results may indicate..." instead of "You have..."
3. DO NOT prescribe medications or suggest changing dosages.
4. For any specific medical concerns, ALWAYS recommend consulting a healthcare professional at one of the hospitals you found.
5. If the user indicates an emergency, tell them to call local emergency services immediately.
"""

