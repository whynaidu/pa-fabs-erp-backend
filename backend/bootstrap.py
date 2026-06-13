"""Idempotent DB bootstrap run on app startup.

Creates tables (so a fresh Render Postgres is usable on first boot) and seeds
the 18 looms + default admin/user accounts only when missing. Safe to run on
every startup — it never wipes existing data.
"""
from sqlalchemy import text
from backend.database import engine, Base, SessionLocal
from backend.models import *  # noqa: F401,F403  (register all models on Base)
from backend.models.loom import Loom
from backend.models.user import User
from backend.services.auth_service import get_password_hash


# Columns added after the tables were first created. create_all() only creates
# missing TABLES, never adds columns to existing ones — so on Postgres we ALTER
# them in (idempotent via IF NOT EXISTS). New/SQLite DBs already have them.
_NEW_COLUMNS = [
    ("purchase_orders", "reed_on", "VARCHAR(10)"),
    ("purchase_orders", "pick_on", "VARCHAR(10)"),
    ("purchase_orders", "warp_count", "VARCHAR(50)"),
    ("purchase_orders", "weft_count", "VARCHAR(50)"),
    ("purchase_orders", "total_ends", "INTEGER"),
    ("purchase_orders", "shortage_percentage", "NUMERIC(5,2)"),
    ("inward_entries", "location", "VARCHAR(120)"),
    ("deliveries", "total_weight", "NUMERIC(10,2)"),
]


def _migrate_columns() -> None:
    if engine.dialect.name != "postgresql":
        return  # SQLite dev DBs are created fresh with the full schema
    with engine.begin() as conn:
        for table, col, coltype in _NEW_COLUMNS:
            conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {coltype}'))
    # Add the new 'weaving' value to the outward process-type enum. ALTER TYPE ADD
    # VALUE must run outside a transaction, so use an autocommit connection. The
    # enum type name is discovered (it backs the existing 'warping' value).
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        row = conn.execute(text(
            "SELECT t.typname FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE e.enumlabel = 'warping' LIMIT 1"
        )).fetchone()
        if row:
            try:
                conn.execute(text(f"ALTER TYPE {row[0]} ADD VALUE IF NOT EXISTS 'weaving'"))
            except Exception:
                pass


def init_and_seed() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_columns()

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
