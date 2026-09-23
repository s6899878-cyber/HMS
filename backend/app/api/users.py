from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.health_profile import HealthProfile
from app.schemas.user import UserOut, HealthProfileOut, HealthProfileUpdate

router = APIRouter()

@router.get("/me", response_model=UserOut)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/me/health-profile", response_model=HealthProfileOut)
def read_user_health_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")
    return profile

@router.put("/me/health-profile", response_model=HealthProfileOut)
def update_user_health_profile(
    profile_in: HealthProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    
    if not profile:
        profile = HealthProfile(user_id=current_user.id, **profile_in.dict(exclude_unset=True))
        db.add(profile)
    else:
        for var, value in profile_in.dict(exclude_unset=True).items():
            setattr(profile, var, value)
            
    db.commit()
    db.refresh(profile)
    return profile
