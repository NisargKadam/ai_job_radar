from fastapi import APIRouter

from app.agent.nodes.deliver import deliver_approved
from app.schemas import SendResultOut

router = APIRouter(tags=["send"])


@router.post("/send", response_model=SendResultOut)
def send_now() -> SendResultOut:
    """Send all approved candidates now (respects the dry_run setting)."""
    return deliver_approved()
