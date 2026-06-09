from fastapi import APIRouter

from app.db.models import Candidate, Sent
from app.db.session import SessionLocal
from app.schemas import SentOut

router = APIRouter(tags=["history"])


@router.get("/history", response_model=list[SentOut])
def history() -> list[SentOut]:
    with SessionLocal() as s:
        rows = s.query(Sent).order_by(Sent.id.desc()).limit(200).all()
        out: list[SentOut] = []
        for r in rows:
            cand = s.get(Candidate, r.candidate_id) if r.candidate_id else None
            out.append(
                SentOut(
                    id=r.id,
                    channel=r.channel,
                    group_id=r.group_id,
                    sent_at=r.sent_at,
                    message=r.message,
                    role_title=cand.role_title if cand else None,
                    company=cand.company if cand else None,
                )
            )
        return out
