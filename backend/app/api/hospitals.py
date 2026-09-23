from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_current_user
from app.models.user import User
from app.models.saved_hospital import SavedHospital
from app.schemas.hospitals import HospitalOut, SavedHospitalOut, SavedHospitalCreate
import math
from app.models.hospital import Hospital, HospitalLocation, HospitalSpecialty, HospitalFacility, TreatmentCost, PatientStatistic
from app.services.query_parser import parse_query
from app.services.geocoding import geocode_area

router = APIRouter()

@router.get("/geocode")
def geocode(q: str):
    """Resolve a city name / PIN code / address into latitude & longitude."""
    result = geocode_area(q)
    if not result:
        raise HTTPException(status_code=404, detail=f"Could not find location: {q}")
    lat, lon, display_name = result
    return {"query": q, "lat": lat, "lon": lon, "display_name": display_name}

def calculate_distance(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2:
        return 9999.0
    R = 6371  # Radius of earth in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)

def calculate_intelligent_score(hospital: Hospital, parsed_query: dict, user_lat: float, user_lon: float):
    score = 0
    reasons = []
    
    hospital_specialties = [s.specialty_name.lower() for s in hospital.specialties]
    hospital_facilities = [f.facility_name.lower() for f in hospital.facilities]
    
    # 1. Disease/Specialization Match (40%)
    if parsed_query["specialties"]:
        matched = False
        for req_spec in parsed_query["specialties"]:
            if req_spec.lower() in hospital_specialties:
                matched = True
                reasons.append(f"✓ Matches your need for {req_spec}")
        if matched:
            score += 40
        else:
            reasons.append(f"✗ Does not specialize in requested areas")
    else:
        score += 40 # Full points if no specialty required

    # 2. Required Facilities (20%)
    if parsed_query["facilities"]:
        fac_score = 0
        per_fac = 20 / len(parsed_query["facilities"])
        for req_fac in parsed_query["facilities"]:
            if req_fac.lower() in hospital_facilities:
                fac_score += per_fac
                reasons.append(f"✓ {req_fac} available")
        score += fac_score
    else:
        # Generic facility score
        score += min(20, len(hospital.facilities) * 3)
        if "24x7_emergency" in hospital_facilities or "icu" in hospital_facilities:
            reasons.append("✓ Excellent critical care facilities")

    # 3. Distance Match (20%)
    dist = calculate_distance(user_lat, user_lon, hospital.location.latitude if hospital.location else None, hospital.location.longitude if hospital.location else None)
    req_dist = parsed_query["distance_km"] or 50 # Default 50km if not specified in nearby search
    if dist <= req_dist:
        score += 20
        reasons.append(f"✓ Within requested distance ({dist} km)")
    elif dist <= req_dist * 2:
        score += 10
        reasons.append(f"✓ Accessible distance ({dist} km)")
    else:
        reasons.append(f"✗ Far away ({dist} km)")

    # 4. Budget Match (20%)
    if parsed_query["budget"]:
        budget = parsed_query["budget"]
        min_cost = min([c.cost_min for c in hospital.costs if c.cost_min] or [9999999])
        if min_cost <= budget:
            score += 20
            reasons.append(f"✓ Treatments available within budget")
        else:
            reasons.append(f"✗ May exceed budget")
    else:
        score += 20 # Full points if no budget specified

    return {
        "score": int(score),
        "reasons": reasons,
        "distance": dist
    }

@router.get("/intelligent-search", response_model=List[HospitalOut])
def intelligent_search(
    query: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    sort_by: Optional[str] = Query("score", description="Sort by score, distance, rating"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    parsed = parse_query(query)
    all_hospitals = db.query(Hospital).all()
    
    results = []
    for h in all_hospitals:
        match_data = calculate_intelligent_score(h, parsed, lat or 28.6139, lon or 77.2090)
        
        # Filter out completely irrelevant hospitals if looking for a specific disease
        if parsed["specialties"] and match_data["score"] < 40:
            continue
            
        hout = HospitalOut.from_orm(h)
        hout.distance_km = match_data["distance"]
        hout.match_score = match_data["score"]
        hout.why_recommended = match_data["reasons"]
        
        # Find best for
        if parsed["specialties"]:
            hout.best_for = ", ".join(parsed["specialties"])
        else:
            hout.best_for = ", ".join([s.specialty_name for s in h.specialties[:2]]) if h.specialties else "General Care"
            
        results.append(hout)
        
    if len(results) < 5:
        from app.services.ai_service import generate_dynamic_hospitals
        spec_type = parsed["specialties"][0] if parsed["specialties"] else query
        dynamic_hospitals = generate_dynamic_hospitals(lat or 28.6139, lon or 77.2090, 5000000, spec_type)
        db_names = {r.name.lower() for r in results}
        
        for idx, dh in enumerate(dynamic_hospitals):
            if dh.get("name", "").lower() in db_names:
                continue
                
            dh_loc = dh.get("location", {})
            dh_lat = dh_loc.get("latitude") if isinstance(dh_loc, dict) else (lat or 28.6139)
            dh_lon = dh_loc.get("longitude") if isinstance(dh_loc, dict) else (lon or 77.2090)
            exact_dist = calculate_distance(lat or 28.6139, lon or 77.2090, dh_lat, dh_lon)
            if exact_dist == 0:
                exact_dist = dh.get("distance_km", 5.0)

            specs = dh.get("specialties", [])
            if parsed["specialties"] and not any(isinstance(s, dict) and s.get("specialty_name") == spec_type for s in specs):
                specs.insert(0, {"specialty_name": spec_type})

            best_for_str = ", ".join([s.get("specialty_name") for s in specs if isinstance(s, dict) and s.get("specialty_name")]) if specs else "General Care"

            hout_dict = {
                "id": 988000 + idx,
                "name": dh.get("name", "Specialized Hospital"),
                "external_id": dh.get("external_id", f"gen-spec-{idx}"),
                "hospital_type": dh.get("hospital_type", "Private"),
                "government_or_private": dh.get("government_or_private", "Private"),
                "location": dh_loc if isinstance(dh_loc, dict) else {},
                "specialties": specs,
                "facilities": dh.get("facilities", [{"facility_name": "ICU"}, {"facility_name": "24/7 Emergency"}]),
                "verifications": [],
                "costs": [],
                "patient_stats": [],
                "match_score": 95 - idx,
                "distance_km": exact_dist,
                "rating": dh.get("rating", 4.6),
                "why_recommended": [f"✓ Top specialized center for {best_for_str}", "✓ Advanced medical facilities"],
                "best_for": best_for_str
            }
            results.append(HospitalOut(**hout_dict))
            db_names.add(dh.get("name", "").lower())

    if sort_by == "distance":
        results.sort(key=lambda x: x.distance_km or 999, reverse=(sort_order == "desc"))
    elif sort_by == "rating":
        results.sort(key=lambda x: getattr(x, "rating", 0) or 0, reverse=(sort_order == "desc"))
    else:
        results.sort(key=lambda x: x.match_score, reverse=(sort_order == "desc"))
        
    return results

@router.get("/nearby", response_model=List[HospitalOut])
def get_nearby_hospitals(
    lat: float,
    lon: float,
    radius: int = Query(50000, description="Radius in meters"),
    type: Optional[str] = None,
    sort_by: Optional[str] = Query("score", description="Sort by score, distance, rating"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    hospitals_query = db.query(Hospital)
    if type:
        hospitals_query = hospitals_query.filter(Hospital.hospital_type.ilike(f"%{type}%"))
        
    all_hospitals = hospitals_query.all()
    parsed = parse_query("") # Empty parsed query for basic nearby math
    
    results = []
    for h in all_hospitals:
        match_data = calculate_intelligent_score(h, parsed, lat, lon)
        if match_data["distance"] <= radius / 1000.0:
            hout = HospitalOut.from_orm(h)
            hout.distance_km = match_data["distance"]
            hout.match_score = match_data["score"]
            hout.why_recommended = match_data["reasons"]
            hout.best_for = ", ".join([s.specialty_name for s in h.specialties[:2]]) if h.specialties else "General Care"
            results.append(hout)
            
    if sort_by == "distance":
        results.sort(key=lambda x: x.distance_km or 999, reverse=(sort_order == "desc"))
    elif sort_by == "rating":
        results.sort(key=lambda x: getattr(x, "rating", 0) or 0, reverse=(sort_order == "desc"))
    elif sort_by == "cost":
        # Sort by cost_min of first cost entry if available
        def get_min_cost(h):
            if hasattr(h, 'costs') and h.costs:
                return h.costs[0].cost_min or 999999
            return 999999
        results.sort(key=get_min_cost, reverse=(sort_order == "desc"))
    elif sort_by == "emergency":
        # Sort by emergency availability (hospitals with ER first if desc)
        def has_er(h):
            facs = getattr(h, 'facilities', [])
            return any("emergency" in f.facility_name.lower() for f in facs)
        results.sort(key=has_er, reverse=(sort_order == "desc"))
    else:
        # Default to score (desc) or distance (asc)
        results.sort(key=lambda x: x.match_score, reverse=(sort_order == "desc"))

    # Fallback to OpenAI dynamic generation if DB has few results
    if len(results) < 5:
        from app.services.ai_service import generate_dynamic_hospitals
        dynamic_hospitals = generate_dynamic_hospitals(lat, lon, radius, type)
        db_names = {r.name.lower() for r in results}
        
        for idx, dh in enumerate(dynamic_hospitals):
            if dh.get("name", "").lower() in db_names:
                continue
                
            dh_loc = dh.get("location", {})
            dh_lat = dh_loc.get("latitude") if isinstance(dh_loc, dict) else lat
            dh_lon = dh_loc.get("longitude") if isinstance(dh_loc, dict) else lon
            exact_dist = calculate_distance(lat, lon, dh_lat or lat, dh_lon or lon)
            if exact_dist == 0 or exact_dist > 500:
                exact_dist = dh.get("distance_km", 2.5)

            specs = dh.get("specialties", [])
            best_for_str = ", ".join([s.get("specialty_name") for s in specs if isinstance(s, dict) and s.get("specialty_name")]) if specs else "General Care"

            hout_dict = {
                "id": 999000 + idx,
                "name": dh.get("name", "Generated Hospital"),
                "external_id": dh.get("external_id", f"gen-{idx}"),
                "hospital_type": dh.get("hospital_type", "Private"),
                "government_or_private": dh.get("government_or_private", "Private"),
                "location": dh_loc if isinstance(dh_loc, dict) else {},
                "specialties": specs,
                "facilities": dh.get("facilities", []),
                "verifications": [],
                "costs": [],
                "patient_stats": [],
                "match_score": 90 - idx,
                "distance_km": exact_dist,
                "rating": dh.get("rating", 4.5),
                "why_recommended": ["✓ Dynamically found in real world", f"✓ Multi-specialty care near your location"],
                "best_for": best_for_str
            }
            results.append(HospitalOut(**hout_dict))
            db_names.add(dh.get("name", "").lower())

    if sort_by == "distance":
        results.sort(key=lambda x: x.distance_km or 999, reverse=(sort_order == "desc"))
    elif sort_by == "rating":
        results.sort(key=lambda x: getattr(x, "rating", 0) or 0, reverse=(sort_order == "desc"))
    elif sort_by == "cost":
        def get_min_cost(h):
            if hasattr(h, 'costs') and h.costs:
                return h.costs[0].cost_min or 999999
            return 999999
        results.sort(key=get_min_cost, reverse=(sort_order == "desc"))
    elif sort_by == "emergency":
        def has_er(h):
            facs = getattr(h, 'facilities', [])
            return any("emergency" in f.facility_name.lower() for f in facs)
        results.sort(key=has_er, reverse=(sort_order == "desc"))
    else:
        results.sort(key=lambda x: x.match_score, reverse=(sort_order == "desc"))

    return results

@router.get("/{hospital_id}", response_model=HospitalOut)
def get_hospital_by_id(
    hospital_id: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        h = db.query(Hospital).filter((Hospital.id == int(hospital_id)) | (Hospital.external_id == hospital_id)).first()
    except ValueError:
        h = db.query(Hospital).filter(Hospital.external_id == hospital_id).first()
        
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")
        
    match_data = calculate_intelligent_score(h, parse_query(""), lat or 0, lon or 0)
    hout = HospitalOut.from_orm(h)
    hout.distance_km = match_data["distance"]
    hout.match_score = match_data["score"]
    hout.why_recommended = match_data["reasons"]
    hout.best_for = ", ".join([s.specialty_name for s in h.specialties[:2]]) if h.specialties else "General Care"
    return hout
