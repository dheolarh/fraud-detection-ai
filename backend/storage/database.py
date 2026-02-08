"""
Database connection and session management.
Implements connection pooling and provides database session factory.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
from config.settings import settings
from core.exceptions import DatabaseError
from loguru import logger

# Create declarative base for ORM models
Base = declarative_base()

# Create database engine with connection pooling
try:
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,              # Number of permanent connections
        max_overflow=20,           # Number of additional connections
        pool_pre_ping=True,        # Verify connections before using
        echo=False,                # Set True for SQL logging during development
        future=True                # Use SQLAlchemy 2.0 style
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise DatabaseError(f"Database connection failed: {e}")

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    Use with FastAPI Depends() for automatic session management.
    
    Yields:
        Session: SQLAlchemy database session
    
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise DatabaseError(f"Database operation failed: {e}")
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    Use when not in FastAPI context.
    
    Example:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database context error: {e}")
        raise DatabaseError(f"Database operation failed: {e}")
    finally:
        db.close()


def create_tables():
    """
    Create all database tables.
    Should be called once during initial setup.
    """
    try:
        from storage.models import Base  # Import to register all models
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise DatabaseError(f"Table creation failed: {e}")


def drop_tables():
    """
    Drop all database tables.
    ⚠️ USE WITH CAUTION - This will delete all data!
    """
    try:
        from storage.models import Base
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise DatabaseError(f"Table drop failed: {e}")


def test_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        from sqlalchemy import text
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
