from fastapi import APIRouter, Query
from typing import List, Optional
from services.overpass import get_hospitals_from_overpass
from services.recommendation import calculate_recommendation_score

router = APIRouter()

@router.get("/")
async def get_hospitals(
    lat: float = Query(40.7128, description="Latitude of user location"),
    lon: float = Query(-74.0060, description="Longitude of user location"),
    radius: int = Query(5000, description="Search radius in meters")
):
    # Fetch from Overpass API
    hospitals_raw = get_hospitals_from_overpass(lat, lon, radius)
    
    scored_hospitals = []
    for h in hospitals_raw:
        metrics = calculate_recommendation_score(h, lat, lon)
        
        # Merge data
        scored_hospitals.append({
            "id": h["id"],
            "name": h["name"],
            "lat": h["lat"],
            "lon": h["lon"],
            "recommendation_score": metrics["score"],
            "distance_km": metrics["distance_km"],
            "rating": metrics["simulated_rating"],
            "consultationCost": metrics["consultation_cost"],
            "specialties": ["General"] # Simulated
        })
        
    # Sort by recommendation score descending
    scored_hospitals.sort(key=lambda x: x["recommendation_score"], reverse=True)
    
    return scored_hospitals
