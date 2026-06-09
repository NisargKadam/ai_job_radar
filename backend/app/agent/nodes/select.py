from app.agent.state import AgentState


def select(state: AgentState) -> dict:
    """Keep only job posts, sorted by relevance desc. Surface a low-yield notice
    if fewer than min_posts were found (never pad with non-jobs)."""
    deduped = state.get("deduped", [])
    settings = state.get("settings", {})
    min_posts = settings.get("min_posts", 5)
    errors = list(state.get("errors", []))

    jobs = [c for c in deduped if c["cls"].is_job]
    jobs.sort(key=lambda c: c["cls"].relevance_score, reverse=True)

    if len(jobs) < min_posts:
        errors.append(f"low_yield: only {len(jobs)} job post(s) found (min {min_posts})")

    return {"selected": jobs, "errors": errors}
