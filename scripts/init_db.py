import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import engine, Base
from backend.models import *
from backend.services.auth_service import get_password_hash
from sqlalchemy.orm import sessionmaker


def init_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Seeding 18 looms...")
    looms = []
    for i in range(1, 19):
        loom = Loom(
            loom_number=i,
            status="free"
        )
        looms.append(loom)

    session.query(Loom).delete()
    session.add_all(looms)
    session.commit()
    print("18 looms seeded successfully!")

    admin = session.query(User).filter(User.username == "admin").first()
    if not admin:
        print("Creating admin user...")
        admin = User(
            id="admin_default",
            full_name="Administrator",
            email="admin@pafabs.com",
            username="admin",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_approved=True,
            status="approved"
        )
        session.add(admin)
        session.commit()
        print("Admin user created! Username: admin, Password: admin123")
    else:
        print("Admin user already exists")

    demo_user = session.query(User).filter(User.username == "user").first()
    if not demo_user:
        print("Creating demo user...")
        demo_user = User(
            id="user_default",
            full_name="Demo Staff User",
            email="user@pafabs.com",
            username="user",
            password_hash=get_password_hash("user123"),
            role="user",
            is_approved=True,
            status="approved"
        )
        session.add(demo_user)
        session.commit()
        print("Demo user created! Username: user, Password: user123")
    else:
        print("Demo user already exists")

    session.close()
    print("\nDatabase initialization complete!")


if __name__ == "__main__":
    init_database()