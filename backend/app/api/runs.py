from fastapi import APIRouter, HTTPException

from app.db.models import Run, RunEvent
from app.db.session import SessionLocal
from app.runner import run_manager
from app.schemas import RunDetailOut, RunEventOut, RunOut

router = APIRouter(tags=["runs"])


@router.post("/run")
async def trigger_run() -> dict:
    was_running = run_manager.is_running
    run_id = await run_manager.start()
    return {"run_id": run_id, "already_running": was_running}


@router.get("/runs", response_model=list[RunOut])
def list_runs() -> list[RunOut]:
    with SessionLocal() as s:
        rows = s.query(Run).order_by(Run.id.desc()).limit(50).all()
        return [RunOut.model_validate(r) for r in rows]


@router.get("/runs/{run_id}", response_model=RunDetailOut)
def get_run(run_id: int) -> RunDetailOut:
    with SessionLocal() as s:
        run = s.get(Run, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        events = (
            s.query(RunEvent).filter_by(run_id=run_id).order_by(RunEvent.id).all()
        )
        base = RunOut.model_validate(run).model_dump()
        return RunDetailOut(**base, events=[RunEventOut.model_validate(e) for e in events])
