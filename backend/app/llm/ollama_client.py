import httpx

from app.config import config
from app.schemas import Classification, Post

SYSTEM = (
    "You are a strict classifier of LinkedIn posts. Decide whether a post is a "
    "GENUINE job opportunity for AI / ML / LLM / Agentic engineering roles. "
    "Target keywords: {kw}. "
    "A 'job' means the author is hiring or sharing a specific open role (not generic "
    "career advice, news, a course, an event recap, or self-promotion). "
    "If it is not clearly a relevant open role, set is_job=false. "
    "Respond with ONLY a single JSON object and no other text."
)

SCHEMA_HINT = (
    '{"is_job": boolean, "role_title": string|null, "company": string|null, '
    '"location": string|null, "seniority": string|null, '
    '"relevance_score": number between 0 and 1, "one_line_summary": string|null}'
)


def _prompt(post: Post, keywords: list[str], strict: bool) -> str:
    extra = (
        "\nIMPORTANT: your previous reply was NOT valid JSON. Output ONLY the JSON object."
        if strict
        else ""
    )
    return (
        SYSTEM.format(kw=", ".join(keywords))
        + f"\nReturn exactly this shape: {SCHEMA_HINT}{extra}\n\n"
        + f"POST AUTHOR: {post.author}\nPOST TEXT:\n{post.text}\n"
    )


def _call(prompt: str, model: str) -> str:
    r = httpx.post(
        f"{config.ollama_base_url}/api/generate",
        json={"model": model, "prompt": prompt, "format": "json", "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["response"]


def classify_post(post: Post, keywords: list[str], model: str) -> Classification:
    """Classify a post via Ollama. Validates strict JSON with Pydantic; retries
    once with a stricter instruction; falls back to a non-job result (never raises)."""
    for strict in (False, True):
        try:
            raw = _call(_prompt(post, keywords, strict), model)
            return Classification.model_validate_json(raw)
        except Exception:
            continue
    return Classification(is_job=False, relevance_score=0.0)
