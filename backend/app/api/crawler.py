from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.nabh_crawler import sync_hospitals_to_db

router = APIRouter()

@router.post("/run-nabh")
def run_crawler_endpoint(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers the NABH web crawler to fetch and sync hospitals into the database.
    Since web scraping can take time, we can run it either synchronously for demo purposes
    or in the background. We will run it synchronously here to return the exact stats.
    """
    try:
        result = sync_hospitals_to_db(db)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}
