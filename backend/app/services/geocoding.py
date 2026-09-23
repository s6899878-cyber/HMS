"""
Geocoding service: resolve a free-text area (city name or 6-digit PIN code)
into latitude/longitude using the free Nominatim (OpenStreetMap) API.

No API key required - perfect for demos and hackathons.
"""
import httpx
from functools import lru_cache

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "MediConnect/1.0 (hackathon demo app)"}


@lru_cache(maxsize=128)
def geocode_area(query: str):
    """
    Resolve a city name / PIN code / address to (lat, lon).
    Returns None when nothing sensible is found.
    """
    q = (query or "").strip()
    if not q:
        return None

    params = {
        "q": q,
        "format": "json",
        "limit": 1,
        "countrycodes": "in",  # India-focused searches (PIN codes, cities)
    }

    try:
        resp = httpx.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=8.0)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        # Return lat, lon, and full formatted address
        return float(results[0]["lat"]), float(results[0]["lon"]), results[0].get("display_name", q)
    except Exception:
        return None
