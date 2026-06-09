import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.runner import run_manager
from app.settings_service import get_settings

scheduler = AsyncIOScheduler()
JOB_ID = "daily_scan"


async def _scheduled_run() -> None:
    await run_manager.start()


def schedule_daily(time_str: str):
    """(Re)register the daily scan job at HH:MM local time. Returns the Job."""
    try:
        hour, minute = (int(x) for x in time_str.split(":"))
    except ValueError:
        hour, minute = 8, 30
    return scheduler.add_job(
        _scheduled_run,
        CronTrigger(hour=hour, minute=minute),
        id=JOB_ID,
        replace_existing=True,
    )


def start_scheduler() -> None:
    if os.environ.get("AIJR_DISABLE_SCHEDULER"):
        return
    if not scheduler.running:
        scheduler.start()
    schedule_daily(get_settings().schedule_time)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def reschedule(time_str: str) -> None:
    """Called after the schedule_time setting changes."""
    if scheduler.running:
        schedule_daily(time_str)
