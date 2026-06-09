from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

DEFAULT_KEYWORDS = [
    "AI Engineer",
    "Agentic AI",
    "Agentic Engineer",
    "AI Engineering",
    "LLM Engineer",
    "ML Engineer",
    "Applied AI",
    "Machine Learning Engineer",
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running")  # running|finished|error
    posts_seen: Mapped[int] = mapped_column(Integer, default=0)
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"), nullable=True)
    permalink: Mapped[str] = mapped_column(String(1024), unique=True)
    author: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    company: Mapped[str | None] = mapped_column(String(512), nullable=True)
    location: Mapped[str | None] = mapped_column(String(512), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(128), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|approved|rejected|sent
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Sent(Base):
    __tablename__ = "sent"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("candidates.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(32))
    group_id: Mapped[str] = mapped_column(String(128))
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    message: Mapped[str] = mapped_column(Text)


class Seen(Base):
    __tablename__ = "seen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    permalink: Mapped[str] = mapped_column(String(1024), unique=True)
    first_seen_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class RunEvent(Base):
    __tablename__ = "run_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    ts: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    level: Mapped[str] = mapped_column(String(16), default="info")  # info|warn|error
    message: Mapped[str] = mapped_column(Text)


class SettingsRow(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    keywords: Mapped[list] = mapped_column(JSON, default=lambda: list(DEFAULT_KEYWORDS))
    schedule_time: Mapped[str] = mapped_column(String(8), default="08:30")
    min_posts: Mapped[int] = mapped_column(Integer, default=5)
    auto_send: Mapped[bool] = mapped_column(Boolean, default=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    delivery_channel: Mapped[str] = mapped_column(String(32), default="telegram")
    group_ids: Mapped[list] = mapped_column(JSON, default=list)
    ollama_model: Mapped[str] = mapped_column(String(128), default="gemma4:12b")
    fixture_mode: Mapped[bool] = mapped_column(Boolean, default=False)
