from app.agent.state import AgentState
from app.db.models import Candidate
from app.db.session import SessionLocal


def dedup(state: AgentState) -> dict:
    """Drop posts whose permalink was already surfaced as a Candidate.
    (Sent rows reference candidates, so checking Candidate covers sent too.)"""
    classified = state.get("classified", [])
    with SessionLocal() as s:
        existing = {p for (p,) in s.query(Candidate.permalink).all()}
    deduped = [c for c in classified if c["post"].permalink not in existing]
    return {"deduped": deduped}
