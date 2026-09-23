from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

# For async operations
# Replace postgresql:// with postgresql+asyncpg:// if using async engine, but Neon works well with psycopg2
# Here we will use synchronous engine with SQLAlchemy 2.0 for simplicity and robustness, or async if required.
# The user asked for "async database operations where appropriate". 
# Let's use asyncpg if possible, but standard create_engine with psycopg2 is safer if asyncpg isn't installed.
# We will use standard psycopg2-binary synchronous engine for reliability, wrapped in async routes.

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
