from typing import TypedDict

from app.schemas import Post


class AgentState(TypedDict, total=False):
    run_id: int
    dry_run: bool
    auto_send: bool
    settings: dict
    raw_posts: list[Post]
    classified: list[dict]  # {"post": Post, "cls": Classification}
    deduped: list[dict]
    selected: list[dict]
    errors: list[str]
