import httpx

def get_hospitals_from_overpass(lat: float, lon: float, radius: int = 5000):
    """
    Fetches nearby hospitals from the Overpass API (OpenStreetMap).
    radius is in meters (default 5000m = 5km).
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      way["amenity"="hospital"](around:{radius},{lat},{lon});
      relation["amenity"="hospital"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    try:
        headers = {"User-Agent": "MediConnect/1.0 (Demo)", "Accept": "*/*"}
        response = httpx.get(overpass_url, params={'data': overpass_query}, headers=headers, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        
        hospitals = []
        for element in data.get("elements", []):
            name = element.get("tags", {}).get("name")
            if not name:
                continue # Skip unnamed hospitals to improve quality
                
            element_lat = element.get("lat") or element.get("center", {}).get("lat")
            element_lon = element.get("lon") or element.get("center", {}).get("lon")
            
            hospitals.append({
                "id": element.get("id"),
                "name": name,
                "lat": element_lat,
                "lon": element_lon,
                "tags": element.get("tags", {})
            })
            
        return hospitals
    except Exception as e:
        print(f"Error fetching from Overpass API: {e}")
        return []
