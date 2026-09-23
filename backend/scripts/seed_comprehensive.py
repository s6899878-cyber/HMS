import sys
import os
from datetime import datetime

# Add the parent directory to sys.path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.hospital import Hospital, HospitalLocation, HospitalVerification, HospitalSpecialty, HospitalFacility, TreatmentCost, PatientStatistic
from app.core.database import Base

from sqlalchemy import text

def seed_db():
    print("Force-killing other connections and dropping old tables...")
    db = SessionLocal()
    try:
        # Kill all other connections to the database to prevent locking
        db.execute(text("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = current_database()
              AND pid <> pg_backend_pid();
        """))
        db.commit()
        
        tables = [
            "patient_statistics", "treatment_costs", "hospital_facilities", 
            "hospital_specialties", "hospital_verifications", "hospital_locations", 
            "saved_hospitals", "hospitals"
        ]
        for table in tables:
            db.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
        db.commit()
    except Exception as e:
        print(f"Error dropping tables: {e}")
        db.rollback()
        
    print("Creating new comprehensive tables...")
    Base.metadata.create_all(bind=engine)
    
    try:
        # AIIMS Delhi
        aiims = Hospital(
            external_id="h_aiims_delhi",
            name="All India Institute of Medical Sciences (AIIMS)",
            hospital_group="AIIMS",
            hospital_type="Super-specialty, Teaching Hospital",
            government_or_private="Government",
            phone="+91-11-26588500",
            emergency_phone="+91-11-26594405",
            email="director@aiims.edu",
            official_website="https://www.aiims.edu/"
        )
        db.add(aiims)
        db.flush()

        db.add(HospitalLocation(
            hospital_id=aiims.id,
            address="Sri Aurobindo Marg, Ansari Nagar, Ansari Nagar East",
            city="New Delhi",
            district="South Delhi",
            state="Delhi",
            union_territory=True,
            pincode="110029",
            latitude=28.5672,
            longitude=77.2100,
            google_maps_url="https://goo.gl/maps/1"
        ))

        db.add(HospitalVerification(
            hospital_id=aiims.id,
            verified=True,
            verification_status="Active",
            accreditation_name="NABH",
            source="NABH Directory",
            last_verified=datetime.utcnow()
        ))

        specialties = ["Cardiology", "Neurology", "Oncology", "Nephrology", "Urology", "Pediatrics"]
        for s in specialties:
            db.add(HospitalSpecialty(hospital_id=aiims.id, specialty_name=s))

        facilities = ["ICU", "NICU", "Emergency", "24x7_Emergency", "Blood_Bank", "MRI", "CT", "PET_CT", "Organ_Transplant"]
        for f in facilities:
            db.add(HospitalFacility(hospital_id=aiims.id, facility_name=f))

        db.add(TreatmentCost(
            hospital_id=aiims.id,
            disease="Heart disease",
            treatment="CABG",
            cost_min=80000,
            cost_max=150000,
            currency="INR",
            cost_type="Government package rate",
            package_type="General Ward",
            source="AIIMS Tariff 2024",
            last_verified=datetime.utcnow()
        ))
        
        db.add(TreatmentCost(
            hospital_id=aiims.id,
            disease="Breast cancer",
            treatment="Chemotherapy",
            cost_min=2000,
            cost_max=10000,
            currency="INR",
            cost_type="Government package rate",
            source="AIIMS Tariff 2024",
            last_verified=datetime.utcnow()
        ))

        db.add(PatientStatistic(
            hospital_id=aiims.id,
            metric_type="annual_patient_volume",
            volume=3500000,
            period="FY2024",
            source="AIIMS Annual Report 2024",
            last_verified=datetime.utcnow()
        ))


        # Tata Memorial Mumbai
        tmc = Hospital(
            external_id="h_tmc_mumbai",
            name="Tata Memorial Hospital",
            hospital_group="TMC",
            hospital_type="Specialty, Cancer Hospital",
            government_or_private="Government/Trust",
            phone="+91-22-24177000",
            emergency_phone="+91-22-24177000",
            official_website="https://tmc.gov.in/"
        )
        db.add(tmc)
        db.flush()

        db.add(HospitalLocation(
            hospital_id=tmc.id,
            address="Dr. E Borges Road, Parel",
            city="Mumbai",
            district="Mumbai City",
            state="Maharashtra",
            union_territory=False,
            pincode="400012",
            latitude=19.0048,
            longitude=72.8427,
            google_maps_url="https://goo.gl/maps/2"
        ))

        db.add(HospitalVerification(
            hospital_id=tmc.id,
            verified=True,
            verification_status="Active",
            accreditation_name="JCI",
            source="JCI Directory",
            last_verified=datetime.utcnow()
        ))

        specialties = ["Oncology", "Surgical Oncology", "Medical Oncology", "Radiation Oncology"]
        for s in specialties:
            db.add(HospitalSpecialty(hospital_id=tmc.id, specialty_name=s))

        facilities = ["ICU", "Blood_Bank", "MRI", "PET_CT", "Radiotherapy"]
        for f in facilities:
            db.add(HospitalFacility(hospital_id=tmc.id, facility_name=f))

        db.add(TreatmentCost(
            hospital_id=tmc.id,
            disease="Breast cancer",
            treatment="Surgery",
            cost_min=30000,
            cost_max=150000,
            currency="INR",
            cost_type="Government package rate",
            source="TMC Subsidy Chart 2023",
            last_verified=datetime.utcnow()
        ))

        db.add(PatientStatistic(
            hospital_id=tmc.id,
            metric_type="annual_patient_volume",
            disease="Cancer",
            volume=65000,
            period="FY2023",
            source="TMC Annual Report",
            last_verified=datetime.utcnow()
        ))

        
        # Medanta Gurugram
        medanta = Hospital(
            external_id="h_medanta_ggn",
            name="Medanta - The Medicity",
            hospital_group="Medanta",
            hospital_type="Super-specialty",
            government_or_private="Private",
            phone="+91-124-4141414",
            emergency_phone="+91-124-4141414",
            official_website="https://www.medanta.org/"
        )
        db.add(medanta)
        db.flush()

        db.add(HospitalLocation(
            hospital_id=medanta.id,
            address="CH Baktawar Singh Road, Sector 38",
            city="Gurugram",
            district="Gurugram",
            state="Haryana",
            union_territory=False,
            pincode="122001",
            latitude=28.4357,
            longitude=77.0427,
            google_maps_url="https://goo.gl/maps/3"
        ))
        
        db.add(HospitalVerification(
            hospital_id=medanta.id,
            verified=True,
            verification_status="Active",
            accreditation_name="JCI",
            source="JCI Directory",
            last_verified=datetime.utcnow()
        ))

        specialties = ["Cardiology", "Cardiac Surgery", "Neurology", "Neurosurgery", "Liver Transplant", "Kidney Transplant"]
        for s in specialties:
            db.add(HospitalSpecialty(hospital_id=medanta.id, specialty_name=s))

        facilities = ["ICU", "Emergency", "24x7_Emergency", "Organ_Transplant", "Robotic_Surgery", "Cath_Lab"]
        for f in facilities:
            db.add(HospitalFacility(hospital_id=medanta.id, facility_name=f))

        db.add(TreatmentCost(
            hospital_id=medanta.id,
            disease="Heart disease",
            treatment="CABG",
            cost_min=300000,
            cost_max=600000,
            currency="INR",
            cost_type="Estimated market range",
            package_type="Private Room",
            source="Third-party aggregator estimation",
            last_verified=datetime.utcnow()
        ))
        
        db.add(TreatmentCost(
            hospital_id=medanta.id,
            disease="Liver disease",
            treatment="Liver Transplant",
            cost_min=1800000,
            cost_max=2500000,
            currency="INR",
            cost_type="Estimated market range",
            source="News report 2024",
            last_verified=datetime.utcnow()
        ))


        db.commit()
        print("Successfully seeded comprehensive database.")
        
    except Exception as e:
        db.rollback()
        print(f"Failed to seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
