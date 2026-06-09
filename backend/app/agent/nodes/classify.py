from app.agent.state import AgentState
from app.db.models import Seen
from app.db.session import SessionLocal
from app.llm.ollama_client import classify_post


def classify(state: AgentState) -> dict:
    """Classify each not-yet-seen post via Ollama. Records every newly classified
    permalink in the Seen ledger (cost guard so we never re-run the LLM on it)."""
    raw = state.get("raw_posts", [])
    settings = state.get("settings", {})
    keywords = settings.get("keywords", [])
    model = settings.get("ollama_model", "gemma4:12b")
    run_id = state.get("run_id")
    errors = list(state.get("errors", []))
    classified: list[dict] = []

    # de-dup within this batch by permalink (defensive)
    batch: dict[str, object] = {}
    for post in raw:
        batch.setdefault(post.permalink, post)

    with SessionLocal() as s:
        seen = {p for (p,) in s.query(Seen.permalink).all()}
        for permalink, post in batch.items():
            if permalink in seen:
                continue
            try:
                cls = classify_post(post, keywords, model)
            except Exception as e:  # classify_post has its own fallback; belt & suspenders
                errors.append(f"classify_failed:{permalink}:{e}")
                continue
            classified.append({"post": post, "cls": cls})
            s.add(Seen(permalink=permalink, first_seen_run_id=run_id))
        s.commit()

    return {"classified": classified, "errors": errors}
