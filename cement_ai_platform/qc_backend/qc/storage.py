from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import json

class SampleORM(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime
    SiO2_in: float
    CaO_in: float
    Moisture: float
    Separator: float
    Gypsum: float
    LSF_est: float
    Blaine_est: float
    fCaO_est: float
    energy_consumption: float

class AuditORM(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime
    kind: str
    detail_json: str

def init_engine(db_path: str):
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine

def add_sample(engine, s: SampleORM):
    with Session(engine) as sess:
        sess.add(s); sess.commit()

def recent_samples(engine, seconds: int):
    # quick and simple; in production add index + ts filter
    with Session(engine) as sess:
        q = select(SampleORM).order_by(SampleORM.ts.desc()).limit(seconds*2)
        rows = list(reversed(sess.exec(q).all()))
        return rows

def log_audit(engine, kind: str, detail: Dict[str, Any]):
    def convert_datetime_to_iso(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    with Session(engine) as sess:
        ao = AuditORM(ts=datetime.utcnow(), kind=kind, detail_json=json.dumps(detail, default=convert_datetime_to_iso))
        sess.add(ao); sess.commit()

def get_audits(engine, limit=100):
    with Session(engine) as sess:
        q = select(AuditORM).order_by(AuditORM.ts.desc()).limit(limit)
        rows = sess.exec(q).all()
        return rows
