"""
Database connection for Banking Backend
Connects to hooverbank PostgreSQL database
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# HooverBank database connection
DATABASE_URL = "postgresql://fraudai_user:password123@localhost:5432/hooverbank"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
