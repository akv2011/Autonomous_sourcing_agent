import datetime
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./sourcing_cache.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Cache(Base):
    __tablename__ = "cache"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, unique=True, index=True)
    result = Column(Text)

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    linkedin_url = Column(String, unique=True, index=True)
    scraped_text = Column(String)
    analysis_json = Column(JSON)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_cached_candidate(session, url: str):
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    return session.query(Candidate).filter(
        Candidate.linkedin_url == url,
        Candidate.last_updated >= seven_days_ago
    ).first()

def cache_candidate(session, url: str, text: str, analysis: dict):
    candidate = session.query(Candidate).filter(Candidate.linkedin_url == url).first()
    if candidate:
        candidate.scraped_text = text
        candidate.analysis_json = analysis
        candidate.last_updated = datetime.datetime.utcnow()
    else:
        candidate = Candidate(
            linkedin_url=url,
            scraped_text=text,
            analysis_json=analysis
        )
        session.add(candidate)
    session.commit()
