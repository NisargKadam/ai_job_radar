from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph

from app.agent.nodes.classify import classify
from app.agent.nodes.dedup import dedup
from app.agent.nodes.deliver import deliver
from app.agent.nodes.ingest import ingest
from app.agent.nodes.review_gate import review_gate, route_after_review
from app.agent.nodes.select import select
from app.agent.state import AgentState
from app.db.models import Run, RunEvent
from app.db.session import SessionLocal
from app.settings_service import get_settings_dict


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("ingest", ingest)
    g.add_node("classify", classify)
    g.add_node("dedup", dedup)
    g.add_node("select", select)
    g.add_node("review_gate", review_gate)
    g.add_node("deliver", deliver)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "classify")
    g.add_edge("classify", "dedup")
    g.add_edge("dedup", "select")
    g.add_edge("select", "review_gate")
    g.add_conditional_edges(
        "review_gate", route_after_review, {"deliver": "deliver", "end": END}
    )
    g.add_edge("deliver", END)
    return g.compile()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_pipeline(run_id: int) -> None:
    """Synchronous entrypoint. Loads settings, runs the graph, updates the Run
    row. Designed to be called inside a worker thread (Playwright sync API)."""
    settings = get_settings_dict()
    state: AgentState = {
        "run_id": run_id,
        "dry_run": settings["dry_run"],
        "auto_send": settings["auto_send"],
        "settings": settings,
        "errors": [],
    }
    try:
        result = build_graph().invoke(state)
        with SessionLocal() as s:
            run = s.get(Run, run_id)
            run.posts_seen = len(result.get("raw_posts", []))
            run.jobs_found = len(result.get("selected", []))
            errs = result.get("errors", [])
            run.error = "; ".join(errs) if errs else None
            run.status = "finished"
            run.finished_at = _utcnow()
            s.add(RunEvent(run_id=run_id, message=f"run finished: {run.jobs_found} job(s) from {run.posts_seen} post(s)"))
            s.commit()
    except Exception as e:  # noqa: BLE001
        with SessionLocal() as s:
            run = s.get(Run, run_id)
            if run:
                run.status = "error"
                run.error = str(e)
                run.finished_at = _utcnow()
                s.add(RunEvent(run_id=run_id, level="error", message=f"run failed: {e}"))
                s.commit()
