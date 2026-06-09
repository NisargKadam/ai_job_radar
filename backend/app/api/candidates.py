from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.models import Candidate
from app.db.session import SessionLocal
from app.schemas import CandidateOut

router = APIRouter(prefix="/candidates", tags=["candidates"])


class BulkApprove(BaseModel):
    ids: list[int] | None = None  # None = approve all pending


def _set_status(cid: int, status: str) -> CandidateOut:
    with SessionLocal() as s:
        c = s.get(Candidate, cid)
        if not c:
            raise HTTPException(status_code=404, detail="candidate not found")
        c.status = status
        s.commit()
        return CandidateOut.model_validate(c)


@router.get("", response_model=list[CandidateOut])
def list_candidates(status: str | None = None) -> list[CandidateOut]:
    with SessionLocal() as s:
        q = s.query(Candidate)
        if status:
            q = q.filter_by(status=status)
        rows = q.order_by(Candidate.relevance_score.desc(), Candidate.id.desc()).all()
        return [CandidateOut.model_validate(c) for c in rows]


@router.post("/{cid}/approve", response_model=CandidateOut)
def approve(cid: int) -> CandidateOut:
    return _set_status(cid, "approved")


@router.post("/{cid}/reject", response_model=CandidateOut)
def reject(cid: int) -> CandidateOut:
    return _set_status(cid, "rejected")


@router.post("/bulk-approve")
def bulk_approve(body: BulkApprove) -> dict:
    with SessionLocal() as s:
        q = s.query(Candidate).filter_by(status="pending")
        if body.ids:
            q = q.filter(Candidate.id.in_(body.ids))
        n = 0
        for c in q.all():
            c.status = "approved"
            n += 1
        s.commit()
    return {"approved": n}
