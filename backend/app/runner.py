import asyncio

from app.db.models import Run
from app.db.session import SessionLocal


class RunManager:
    """Tracks a single active pipeline run executed in a worker thread, so the
    FastAPI event loop stays responsive and Playwright's sync API runs outside
    the loop."""

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._active_run_id: int | None = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def active_run_id(self) -> int | None:
        return self._active_run_id if self.is_running else None

    async def start(self) -> int:
        if self.is_running:
            return self._active_run_id  # type: ignore[return-value]
        with SessionLocal() as s:
            run = Run(status="running")
            s.add(run)
            s.commit()
            run_id = run.id
        self._active_run_id = run_id
        self._task = asyncio.create_task(asyncio.to_thread(self._run, run_id))
        return run_id

    @staticmethod
    def _run(run_id: int) -> None:
        from app.agent.graph import run_pipeline  # lazy import avoids cycles

        run_pipeline(run_id)


run_manager = RunManager()
