import asyncio

from fastapi import APIRouter

from app.scraper.linkedin import open_for_login

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


@router.post("/reauth")
async def reauth() -> dict:
    """Open a headful browser for MANUAL LinkedIn login. The persistent
    user-data-dir keeps the session afterwards. Runs in a worker thread so the
    Playwright sync API is not inside the event loop."""
    asyncio.create_task(asyncio.to_thread(open_for_login))
    return {
        "status": "browser_opened",
        "message": "A browser window opened. Log into LinkedIn, then close the window.",
    }
