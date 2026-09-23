import re

DISEASE_TO_SPECIALTY = {
    # Cardiovascular
    "heart": "Cardiology",
    "cardiac": "Cardiology",
    "coronary": "Cardiology",
    "arrhythmia": "Cardiology",
    "valve": "Cardiology",
    "hypertension": "Cardiology",
    "cabg": "Cardiac Surgery",
    
    # Cancer
    "cancer": "Oncology",
    "tumor": "Oncology",
    "leukemia": "Medical Oncology",
    "lymphoma": "Medical Oncology",
    "breast cancer": "Oncology",
    
    # Kidney
    "kidney": "Nephrology",
    "renal": "Nephrology",
    "dialysis": "Nephrology",
    "kidney transplant": "Kidney Transplant",
    
    # Neurological
    "brain": "Neurology",
    "neuro": "Neurology",
    "stroke": "Neurology",
    "epilepsy": "Neurology",
    "parkinson": "Neurology",
    "alzheimer": "Neurology",
    
    # Orthopedic
    "bone": "Orthopedics",
    "knee": "Orthopedics",
    "hip": "Orthopedics",
    "fracture": "Orthopedics",
    "spine": "Spine Surgery",
    "joint": "Joint Replacement",
    
    # Liver/Digestive
    "liver": "Hepatology",
    "hepatitis": "Hepatology",
    "stomach": "Gastroenterology",
    "gallbladder": "Gastroenterology",
    "pancreas": "Gastroenterology",
    
    # Respiratory
    "lungs": "Pulmonology",
    "asthma": "Pulmonology",
    "copd": "Pulmonology",
    
    # Children
    "child": "Pediatrics",
    "pediatric": "Pediatrics",
    
    # Women
    "women": "Gynecology",
    "pregnancy": "Obstetrics",
    
    # General
    "diabetes": "Diabetology",
    "eye": "Ophthalmology",
    "cataract": "Ophthalmology",
    "mental": "Psychiatry",
    "depression": "Psychiatry"
}

FACILITY_KEYWORDS = {
    "emergency": "Emergency",
    "24x7": "24x7_Emergency",
    "icu": "ICU",
    "nicu": "NICU",
    "pet scan": "PET_CT",
    "mri": "MRI",
    "blood bank": "Blood_Bank",
    "robotic": "Robotic_Surgery"
}

def extract_budget(query: str):
    # Match phrases like "under 5 lakh", "under 500000", "budget 2 lakh"
    match = re.search(r'(under|below|budget)\s*(?:of|is)?\s*(\d+(?:\.\d+)?)\s*(lakh|k|thousand|000)?', query, re.IGNORECASE)
    if not match:
        return None
        
    num = float(match.group(2))
    modifier = match.group(3)
    if modifier:
        modifier = modifier.lower()
        if modifier == "lakh":
            num *= 100000
        elif modifier in ["k", "thousand", "000"]:
            num *= 1000
            
    return num

def extract_distance(query: str):
    match = re.search(r'(within|under|near)\s*(\d+)\s*km', query, re.IGNORECASE)
    if match:
        return float(match.group(2))
    return None

COMMON_SPECIALTIES = [
    "Cardiology", "Cardiac Surgery", "Oncology", "Medical Oncology", "Surgical Oncology",
    "Nephrology", "Neurology", "Neurosurgery", "Orthopedics", "Joint Replacement",
    "Spine Surgery", "Gastroenterology", "Hepatology", "Pulmonology", "Pediatrics",
    "Gynecology", "Obstetrics", "Diabetology", "Endocrinology", "Ophthalmology",
    "Psychiatry", "Urology", "Dermatology", "ENT", "General Surgery", "Internal Medicine"
]

def parse_query(query: str):
    q = (query or "").strip().lower()
    
    parsed = {
        "specialties": [],
        "facilities": [],
        "budget": extract_budget(query or ""),
        "distance_km": extract_distance(query or "")
    }
    
    # Extract specialties based on disease keywords
    for keyword, specialty in DISEASE_TO_SPECIALTY.items():
        if keyword in q and specialty not in parsed["specialties"]:
            parsed["specialties"].append(specialty)
            
    # Direct specialty matching
    for specialty in COMMON_SPECIALTIES:
        if specialty.lower() in q and specialty not in parsed["specialties"]:
            parsed["specialties"].append(specialty)

    # Extract facilities
    for keyword, facility in FACILITY_KEYWORDS.items():
        if keyword in q and facility not in parsed["facilities"]:
            parsed["facilities"].append(facility)
            
    return parsed
