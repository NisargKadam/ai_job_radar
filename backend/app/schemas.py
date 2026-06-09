from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Post(BaseModel):
    """A normalized LinkedIn post (from feed or search, or a fixture)."""

    author: str = ""
    text: str = ""
    permalink: str
    timestamp: str | None = None
    source: str = "feed"  # "feed" | "search:<keyword>" | "fixture"


class Classification(BaseModel):
    """Strict structured output from the Ollama classifier."""

    is_job: bool = False
    role_title: str | None = None
    company: str | None = None
    location: str | None = None
    seniority: str | None = None
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    one_line_summary: str | None = None


class SettingsIn(BaseModel):
    keywords: list[str] | None = None
    schedule_time: str | None = None
    min_posts: int | None = None
    auto_send: bool | None = None
    dry_run: bool | None = None
    delivery_channel: str | None = None
    group_ids: list[str] | None = None
    ollama_model: str | None = None
    fixture_mode: bool | None = None
    send_individual: bool | None = None


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    keywords: list[str]
    schedule_time: str
    min_posts: int
    auto_send: bool
    dry_run: bool
    delivery_channel: str
    group_ids: list[str]
    ollama_model: str
    fixture_mode: bool
    send_individual: bool


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int | None
    permalink: str
    author: str | None
    role_title: str | None
    company: str | None
    location: str | None
    seniority: str | None
    relevance_score: float
    summary: str | None
    raw_text: str | None
    status: str
    created_at: datetime


class RunEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ts: datetime
    level: str
    message: str


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    posts_seen: int
    jobs_found: int
    sent_count: int
    error: str | None


class RunDetailOut(RunOut):
    events: list[RunEventOut] = []


class HealthOut(BaseModel):
    status: str
    ollama: bool
    browser_session: bool
    delivery: bool


class SendResultOut(BaseModel):
    sent: int
    failed: int
    dry_run: bool
    details: list[str] = []


class SentOut(BaseModel):
    id: int
    channel: str
    group_id: str
    sent_at: datetime
    message: str
    role_title: str | None = None
    company: str | None = None
