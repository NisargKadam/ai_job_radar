from app.schemas import CandidateOut


def _headline(c: CandidateOut) -> str:
    return " • ".join([x for x in [c.role_title or "Role", c.company, c.location] if x])


def format_digest(cands: list[CandidateOut]) -> str:
    """One message listing all jobs (default Telegram format).
    Plain text — Telegram auto-links bare URLs, no HTML escaping needed."""
    n = len(cands)
    noun = "opportunity" if n == 1 else "opportunities"
    lines = [f"🤖 AI Job Radar — {n} AI/ML job {noun}", ""]
    for i, c in enumerate(cands, 1):
        lines.append(f"{i}. {_headline(c)}")
        if c.seniority:
            lines.append(f"   Seniority: {c.seniority}")
        if c.summary:
            lines.append(f"   {c.summary}")
        lines.append(f"   {c.permalink}")
        lines.append("")
    return "\n".join(lines).strip()


def format_individual(c: CandidateOut) -> str:
    parts = [f"🤖 {_headline(c)}"]
    if c.seniority:
        parts.append(f"Seniority: {c.seniority}")
    if c.summary:
        parts.append(c.summary)
    parts.append(c.permalink)
    return "\n".join(parts)
