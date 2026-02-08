"""
Database initialization for HooverBank
Creates tables in hooverbank database
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base

# HooverBank database connection (using existing PostgreSQL user for now)
DATABASE_URL = "postgresql://fraudai_user:password123@localhost:5432/hooverbank"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ HooverBank database tables created")

if __name__ == "__main__":
    print("Initializing HooverBank database...")
    init_db()
