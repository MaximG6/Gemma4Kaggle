"""
SQLite persistence layer for triage records (Task 2.4).

All triage results are stored in voicebridge.db at the repo root so
the dashboard can list past intakes and the demo can replay records.
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

_DB_PATH = Path(__file__).resolve().parents[1] / "voicebridge.db"
_DB_URL = os.environ.get("VOICEBRIDGE_DB_URL", f"sqlite:///{_DB_PATH}")

_is_memory = ":memory:" in _DB_URL
if _is_memory:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(_DB_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


class TriageRecord(Base):
    __tablename__ = "triage_records"

    record_id    = Column(String(36), primary_key=True, index=True)
    created_at   = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    triage_level = Column(String(10), nullable=False)
    primary_complaint = Column(Text, nullable=False)
    source_language   = Column(String(10), nullable=False)
    referral_needed   = Column(Boolean, nullable=False)
    confidence_score  = Column(Float, nullable=False)
    full_json         = Column(Text, nullable=False)


def init_db() -> None:
    """Create tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)


def save_record(record_id: str, triage_json: dict) -> None:
    """Persist a triage result to SQLite."""
    record = TriageRecord(
        record_id=record_id,
        triage_level=triage_json["triage_level"],
        primary_complaint=triage_json["primary_complaint"],
        source_language=triage_json["source_language"],
        referral_needed=triage_json["referral_needed"],
        confidence_score=triage_json["confidence_score"],
        full_json=json.dumps(triage_json),
    )
    with SessionLocal() as session:
        session.add(record)
        session.commit()


def list_records(limit: int = 50) -> list[dict]:
    """Return the most recent triage records in AppRecord wire format."""
    with SessionLocal() as session:
        rows = (
            session.query(TriageRecord)
            .order_by(TriageRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.record_id,
                "output_json": r.full_json,
                "created_at": r.created_at.isoformat(),
                "audio_file_path": None,
            }
            for r in rows
        ]


def get_record(record_id: str) -> dict | None:
    """Fetch a single record by ID, or None if not found."""
    with SessionLocal() as session:
        row = session.get(TriageRecord, record_id)
        return json.loads(row.full_json) if row else None
