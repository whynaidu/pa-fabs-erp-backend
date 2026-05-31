"""Idempotent DB bootstrap run on app startup.

Creates tables (so a fresh Render Postgres is usable on first boot) and seeds
the 18 looms + default admin/user accounts only when missing. Safe to run on
every startup — it never wipes existing data.
"""
from backend.database import engine, Base, SessionLocal
from backend.models import *  # noqa: F401,F403  (register all models on Base)
from backend.models.loom import Loom
from backend.models.user import User
from backend.services.auth_service import get_password_hash


def init_and_seed() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Loom).count() == 0:
            db.add_all([Loom(loom_number=i, status="free") for i in range(1, 19)])
            db.commit()

        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                id="admin_default",
                full_name="Administrator",
                email="admin@pafabs.com",
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_approved=True,
                status="approved",
            ))
            db.commit()

        if not db.query(User).filter(User.username == "user").first():
            db.add(User(
                id="user_default",
                full_name="Demo Staff User",
                email="user@pafabs.com",
                username="user",
                password_hash=get_password_hash("user123"),
                role="user",
                is_approved=True,
                status="approved",
            ))
            db.commit()
    finally:
        db.close()
