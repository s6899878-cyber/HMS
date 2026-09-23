import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Haversine formula to calculate distance between two coordinates in kilometers.
    """
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_recommendation_score(hospital, user_lat, user_lon):
    """
    Calculates a recommendation score (0-100) for a hospital based on:
    - Distance (closer is better, max 50 points)
    - Simulated Rating (higher is better, max 30 points)
    - Availability/Cost factor (simulated, max 20 points)
    """
    # 1. Distance Score (0-50)
    distance_km = calculate_distance(user_lat, user_lon, hospital["lat"], hospital["lon"])
    # If distance is > 50km, score is 0. If 0km, score is 50.
    distance_score = max(0, 50 - distance_km)

    # 2. Simulated Rating Score (0-30)
    # Since OSM doesn't always have ratings, we simulate one based on the ID for consistency
    simulated_rating = (hospital["id"] % 50) / 10.0  # Gives a rating 0.0 to 4.9
    rating_score = (simulated_rating / 5.0) * 30

    # 3. Simulated Cost/Availability Score (0-20)
    cost_factor = (hospital["id"] % 20)  # Random simulated value
    
    total_score = round(distance_score + rating_score + cost_factor, 1)
    
    return {
        "score": min(100, total_score),
        "distance_km": round(distance_km, 2),
        "simulated_rating": round(simulated_rating, 1),
        "consultation_cost": 50 + (hospital["id"] % 150) # Simulated cost $50-$200
    }
