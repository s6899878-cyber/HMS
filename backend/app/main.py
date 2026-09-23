from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
import app.models  # Ensure models are loaded

# Create all tables (in a production setting, use Alembic)
Base.metadata.create_all(bind=engine)

from app.api import auth, users, reports, health, hospitals, assistant, uploads, analytics, crawler, medicine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Ensure static directory exists
static_dir = os.path.join(os.getcwd(), "app", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up CORS
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler Example (Phase 21)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An internal server error occurred.", "detail": str(exc)},
    )

@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(uploads.router, prefix=f"{settings.API_V1_STR}/uploads", tags=["uploads"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["health"])
app.include_router(hospitals.router, prefix=f"{settings.API_V1_STR}/hospitals", tags=["hospitals"])
app.include_router(assistant.router, prefix=f"{settings.API_V1_STR}/assistant", tags=["assistant"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(crawler.router, prefix=f"{settings.API_V1_STR}/crawler", tags=["crawler"])
app.include_router(medicine.router, prefix=f"{settings.API_V1_STR}/medicine", tags=["medicine"])
