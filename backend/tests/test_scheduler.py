from app.scheduler import schedule_daily


def _fields(job):
    return {f.name: str(f) for f in job.trigger.fields}


def test_schedule_registers_job_at_time():
    job = schedule_daily("08:30")
    f = _fields(job)
    assert f["hour"] == "8"
    assert f["minute"] == "30"


def test_reschedule_replaces_job():
    job = schedule_daily("21:15")
    f = _fields(job)
    assert f["hour"] == "21"
    assert f["minute"] == "15"
