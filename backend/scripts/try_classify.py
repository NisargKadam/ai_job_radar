"""Manual verification for Milestone 2: classify the fixture posts with the
real local Ollama model and print results. Run from backend/:

    ./.venv/bin/python scripts/try_classify.py
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.db.models import DEFAULT_KEYWORDS  # noqa: E402
from app.llm.ollama_client import classify_post  # noqa: E402
from app.schemas import Post  # noqa: E402

FIX = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "sample_posts.json"
MODEL = "gemma4:12b"


def main() -> None:
    posts = [Post(source="fixture", **p) for p in json.loads(FIX.read_text())]
    jobs = 0
    print(f"Classifying {len(posts)} fixture posts with {MODEL}\n" + "=" * 70)
    for i, post in enumerate(posts, 1):
        t0 = time.time()
        cls = classify_post(post, DEFAULT_KEYWORDS, MODEL)
        dt = time.time() - t0
        if cls.is_job:
            jobs += 1
        flag = "JOB " if cls.is_job else "noise"
        print(
            f"[{i}] {flag} score={cls.relevance_score:.2f} "
            f"role={cls.role_title!r} company={cls.company!r} loc={cls.location!r} ({dt:.1f}s)"
        )
        print(f"      author: {post.author[:60]}")
        print(f"      summary: {cls.one_line_summary}")
    print("=" * 70)
    print(f"Detected {jobs} job posts (fixture has 5 genuine jobs + 3 noise).")


if __name__ == "__main__":
    main()
