"""
Database initialization for Banking Backend
Creates tables in hooverbank_db
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base

# Banking backend database
DATABASE_URL = "postgresql://fraudai_user:password123@localhost:5432/hooverbank_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Banking database tables created")

if __name__ == "__main__":
    print("Initializing HooverBank database...")
    init_db()
