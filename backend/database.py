from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Request data
    domain = Column(String(255), index=True)
    full_name = Column(String(255), index=True)
    
    # Response data
    status = Column(String(50), index=True)
    email = Column(String(255), nullable=True)
    catch_all = Column(Boolean, default=False)
    
    # Additional info
    patterns_tested = Column(Text)  # JSON string
    mx_records = Column(Text)  # JSON string
    smtp_logs = Column(Text)  # JSON string
    debug_info = Column(String(500), nullable=True)
    error_message = Column(String(500), nullable=True)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./email_finder.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
