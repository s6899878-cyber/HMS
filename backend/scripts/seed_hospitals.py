import sys
import os

# Add the parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.hospital import Hospital, HospitalLocation, HospitalSpecialty, HospitalFacility, TreatmentCost, PatientStatistic

def seed_db():
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if hospitals already exist
    if db.query(Hospital).count() > 0:
        print("Database already seeded with hospitals.")
        db.close()
        return

    print("Seeding new hospitals...")
    hospitals = [
        {
            "external_id": "seed-1",
            "name": "City Care Hospital",
            "hospital_type": "Multi-specialty",
            "government_or_private": "Private",
            "location": {
                "address": "Sector 17",
                "city": "Chandigarh",
                "district": "Chandigarh",
                "state": "Chandigarh",
                "latitude": 30.7333,
                "longitude": 76.7794,
            },
            "specialties": ["Nephrology", "Cardiology", "General Medicine"],
            "facilities": ["ICU", "24/7 ER"],
            "costs": [{"disease": "General", "treatment": "Surgery", "cost_min": 150000, "cost_max": 300000}],
        },
        {
            "external_id": "seed-2",
            "name": "Metro Health Institute",
            "hospital_type": "Super-specialty",
            "government_or_private": "Private",
            "location": {
                "address": "Sector 34",
                "city": "Chandigarh",
                "district": "Chandigarh",
                "state": "Chandigarh",
                "latitude": 30.7233,
                "longitude": 76.7694,
            },
            "specialties": ["Orthopedics", "Neurology"],
            "facilities": ["ICU", "MRI"],
            "costs": [{"disease": "Orthopedics", "treatment": "Knee Replacement", "cost_min": 80000, "cost_max": 200000}],
        },
        {
            "external_id": "seed-3",
            "name": "Life Line Clinic",
            "hospital_type": "General",
            "government_or_private": "Government",
            "location": {
                "address": "Sector 22",
                "city": "Chandigarh",
                "district": "Chandigarh",
                "state": "Chandigarh",
                "latitude": 30.7433,
                "longitude": 76.7894,
            },
            "specialties": ["Pediatrics", "General Medicine"],
            "facilities": ["Pharmacy"],
            "costs": [{"disease": "General", "treatment": "Consultation", "cost_min": 1000, "cost_max": 5000}],
        },
        {
            "external_id": "seed-4",
            "name": "PGIMER",
            "hospital_type": "Teaching Hospital",
            "government_or_private": "Government",
            "location": {
                "address": "Sector 12",
                "city": "Chandigarh",
                "district": "Chandigarh",
                "state": "Chandigarh",
                "latitude": 30.7673,
                "longitude": 76.7774,
            },
            "specialties": ["Cardiology", "Neurology", "Oncology", "Cancer", "Nephrology", "Kidney"],
            "facilities": ["ICU", "Advanced MRI", "Trauma Center"],
            "costs": [{"disease": "Various", "treatment": "Various", "cost_min": 5000, "cost_max": 100000}],
        }
    ]

    for h_data in hospitals:
        hospital = Hospital(
            external_id=h_data["external_id"],
            name=h_data["name"],
            hospital_type=h_data["hospital_type"],
            government_or_private=h_data["government_or_private"]
        )
        db.add(hospital)
        db.flush() # flush to get hospital.id

        loc_data = h_data["location"]
        location = HospitalLocation(
            hospital_id=hospital.id,
            address=loc_data["address"],
            city=loc_data["city"],
            district=loc_data["district"],
            state=loc_data["state"],
            latitude=loc_data["latitude"],
            longitude=loc_data["longitude"]
        )
        db.add(location)

        for spec in h_data["specialties"]:
            s = HospitalSpecialty(hospital_id=hospital.id, specialty_name=spec)
            db.add(s)

        for facility in h_data["facilities"]:
            f = HospitalFacility(hospital_id=hospital.id, facility_name=facility)
            db.add(f)
            
        for cost in h_data.get("costs", []):
            c = TreatmentCost(
                hospital_id=hospital.id,
                disease=cost["disease"],
                treatment=cost["treatment"],
                cost_min=cost["cost_min"],
                cost_max=cost["cost_max"]
            )
            db.add(c)

    db.commit()
    print("Successfully seeded hospitals!")
    db.close()

if __name__ == "__main__":
    seed_db()
