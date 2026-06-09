from app.agent.nodes import log_event
from app.agent.state import AgentState
from app.db.models import Candidate, Seen
from app.db.session import SessionLocal


def review_gate(state: AgentState) -> dict:
    """Atomically (a) mark every classified permalink in the Seen ledger and
    (b) persist selected candidates as pending. Doing both in one transaction
    means a crash here loses nothing — the next run simply re-scans."""
    selected = state.get("selected", [])
    classified = state.get("classified", [])
    run_id = state.get("run_id")
    created = 0
    with SessionLocal() as s:
        seen = {p for (p,) in s.query(Seen.permalink).all()}

        # cost-guard ledger for future runs (all classified posts, jobs or not)
        for c in classified:
            pl = c["post"].permalink
            if pl not in seen:
                s.add(Seen(permalink=pl, first_seen_run_id=run_id))
                seen.add(pl)

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
        s.commit()

    log_event(run_id, f"review_gate: {created} new candidate(s) queued")
    return {}


def route_after_review(state: AgentState) -> str:
    return "deliver" if state.get("auto_send") else "end"
