import os, json, hashlib, time
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mcp_audit.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class AuditRecord(Base):
    __tablename__ = "audit_records"
    id = Column(Integer, primary_key=True, index=True)
    req_id = Column(String, index=True)
    action = Column(String)
    payload = Column(Text)
    audit_hash = Column(String, unique=True, index=True)
    ts = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)

def persist_audit(req_id: str, action: str, payload_obj: dict):
    payload = json.dumps(payload_obj, sort_keys=True)
    h = hashlib.sha256(payload.encode()).hexdigest()
    rec = AuditRecord(req_id=req_id, action=action, payload=payload, audit_hash=h, ts=time.time())
    db = SessionLocal()
    db.add(rec)
    db.commit()
    db.refresh(rec)
    db.close()
    return rec.audit_hash
