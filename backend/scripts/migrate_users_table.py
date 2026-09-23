"""
One-time migration: legacy `users` table used (id, name, email, password, role, created_at)
but the app model expects (id, name, email, password_hash, created_at, updated_at).

This script:
1. Renames the legacy table + its sequence to users_legacy_<ts> (data preserved, never dropped).
2. Re-points child-table foreign keys (health_profiles, medical_reports, ...) to the new users table.
3. Creates the new users table from the current SQLAlchemy model.
4. Seeds a demo login account (demo@mediconnect.app / demo123).

Run once from backend/:  python scripts/migrate_users_table.py
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from sqlalchemy import text
from app.core.database import engine, Base
import app.models  # noqa: F401  (ensures all models are registered on Base)
from app.core.security import get_password_hash

DEMO_EMAIL = "demo@mediconnect.app"
DEMO_PASSWORD = "demo123"


def migrate():
    legacy_name = f"users_legacy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    conn = engine.connect()
    txn = conn.begin()
    try:
        exists = conn.execute(text(
            "select exists (select 1 from information_schema.tables where table_name='users')"
        )).scalar()
        if not exists:
            print("No legacy users table found - creating fresh from models.")
            Base.metadata.create_all(bind=conn, tables=[Base.metadata.tables["users"]])
            txn.commit()
            return

        legacy_cols = [r[0] for r in conn.execute(text(
            "select column_name from information_schema.columns where table_name='users'"
        )).fetchall()]

        if "password_hash" in legacy_cols:
            print("users table already up to date - nothing to do.")
            txn.commit()
            return

        print(f"Renaming legacy table -> {legacy_name}")
        conn.execute(text(f'ALTER TABLE users RENAME TO {legacy_name}'))

        # Move the PK sequence along with it so the new table can own a fresh one
        conn.execute(text(f"ALTER SEQUENCE users_id_seq RENAME TO {legacy_name}_id_seq"))

        # Drop indexes that belonged to the legacy table
        conn.execute(text("DROP INDEX IF EXISTS ix_users_email"))
        conn.execute(text("DROP INDEX IF EXISTS ix_users_name"))
        conn.execute(text("DROP INDEX IF EXISTS ix_users_id"))

        # Child tables reference users(id) - drop those FKs so they re-bind to the new table
        for table in ["health_profiles", "medical_reports", "health_metrics",
                      "saved_hospitals", "conversations"]:
            conn.execute(text(
                f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_user_id_fkey"
            ))

        print("Creating new users table from model...")
        Base.metadata.create_all(bind=conn, tables=[Base.metadata.tables["users"]])

        # Re-create the FKs against the new users table
        for table in ["health_profiles", "medical_reports", "health_metrics",
                      "saved_hospitals", "conversations"]:
            conn.execute(text(
                f"ALTER TABLE {table} ADD CONSTRAINT {table}_user_id_fkey "
                f"FOREIGN KEY (user_id) REFERENCES users(id)"
            ))
        txn.commit()
    except Exception:
        txn.rollback()
        raise
    finally:
        conn.close()

    # Seed demo user
    from app.core.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == DEMO_EMAIL).first():
            db.add(User(name="Demo User", email=DEMO_EMAIL,
                        password_hash=get_password_hash(DEMO_PASSWORD)))
            db.commit()
            print(f"Seeded demo account: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            print("Demo account already exists.")
    finally:
        db.close()

    print("Migration complete.")


if __name__ == "__main__":
    migrate()
