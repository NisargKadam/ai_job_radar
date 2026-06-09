from app.db.models import RunEvent
from app.db.session import SessionLocal


def log_event(run_id: int | None, message: str, level: str = "info") -> None:
    """Append a timestamped event to a run's log (no-op without a run_id)."""
    if run_id is None:
        return
    with SessionLocal() as s:
        s.add(RunEvent(run_id=run_id, level=level, message=message))
        s.commit()
