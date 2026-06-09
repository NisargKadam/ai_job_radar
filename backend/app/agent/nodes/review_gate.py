from app.agent.state import AgentState
from app.db.models import Candidate, RunEvent
from app.db.session import SessionLocal


def review_gate(state: AgentState) -> dict:
    """Persist selected candidates as pending (idempotent on permalink).
    The routing function decides whether to deliver or END."""
    selected = state.get("selected", [])
    run_id = state.get("run_id")
    created = 0
    with SessionLocal() as s:
        for c in selected:
            post, cls = c["post"], c["cls"]
            if s.query(Candidate).filter_by(permalink=post.permalink).first():
                continue
            s.add(
                Candidate(
                    run_id=run_id,
                    permalink=post.permalink,
                    author=post.author,
                    role_title=cls.role_title,
                    company=cls.company,
                    location=cls.location,
                    seniority=cls.seniority,
                    relevance_score=cls.relevance_score,
                    summary=cls.one_line_summary,
                    raw_text=post.text,
                    status="pending",
                )
            )
            created += 1
        if run_id is not None:
            s.add(RunEvent(run_id=run_id, message=f"review_gate: {created} new candidate(s) queued"))
        s.commit()
    return {}


def route_after_review(state: AgentState) -> str:
    return "deliver" if state.get("auto_send") else "end"
