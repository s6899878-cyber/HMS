# MediConnect Backend

Professional FastAPI + PostgreSQL healthcare backend for the MediConnect application.

## Architecture
- **Framework**: FastAPI (Python 3.12+)
- **Database**: Neon PostgreSQL via SQLAlchemy (ORM) and Alembic (Migrations)
- **Authentication**: JWT based stateless auth with bcrypt password hashing
- **File Storage**: Cloudinary integration for medical reports
- **AI**: OpenAI API for Health Assistant and Report Analysis

## Setup & Run

### 1. Environment
Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

Install requirements:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and fill in your secrets.
- `DATABASE_URL`: Your Neon connection string
- `OPENAI_API_KEY`: OpenAI secret key
- `CLOUDINARY_*`: Cloudinary credentials
- `JWT_SECRET_KEY`: Random secure string

### 3. Database Migrations
Generate initial tables in PostgreSQL:
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload
```
API runs on `http://localhost:8000`
Swagger UI Docs: `http://localhost:8000/docs`

## Security
- This API isolates data by enforcing a `get_current_user` dependency on all protected routes.
- Never commit the `.env` file containing secrets.
- Medical reports are NOT stored in PostgreSQL blobs; they are safely offloaded to Cloudinary with secure URL generation.
- CORS is restricted to `http://localhost:5173`.
