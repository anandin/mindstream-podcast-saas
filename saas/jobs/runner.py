"""Background job runner using APScheduler."""
import os
import logging
import uuid
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

log = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    """Start the APScheduler background scheduler if not already running."""
    if not scheduler.running:
        scheduler.start()
        log.info("Job scheduler started")


def stop_scheduler() -> None:
    """Shut down the APScheduler background scheduler."""
    if scheduler.running:
        scheduler.shutdown()


def enqueue_job(job_type: str, payload: dict, delay_seconds: int = 0) -> str:
    """Enqueue a background job. Returns job_id."""
    from saas.db.models import Job, get_session
    from datetime import timedelta

    db = get_session(os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db"))
    job = Job(
        id=str(uuid.uuid4()),
        type=job_type,
        payload=payload,
        status="queued",
        scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=delay_seconds),
    )
    db.add(job)
    db.commit()
    job_id = job.id
    db.close()
    scheduler.add_job(
        _run_job,
        "date",
        run_date=job.scheduled_at,
        args=[job_id],
        misfire_grace_time=300,
    )
    return job_id


def _run_job(job_id: str) -> None:
    """Execute a job by ID, updating its status throughout."""
    from saas.db.models import Job, get_session

    db = get_session(os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db"))
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        db.close()
        return

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    job.attempts += 1
    db.commit()

    try:
        result = _dispatch(job.type, job.payload)
        job.status = "done"
        job.completed_at = datetime.now(timezone.utc)
        job.result = result
    except Exception as e:
        log.exception("Job %s failed", job_id)
        job.status = "failed" if job.attempts >= job.max_attempts else "queued"
        job.error = str(e)

    db.commit()
    db.close()


def _dispatch(job_type: str, payload: dict) -> dict:
    """Dispatch a job to the appropriate handler."""
    if job_type == "process_memo":
        return _process_memo(payload)
    raise ValueError(f"Unknown job type: {job_type}")


def _process_memo(payload: dict) -> dict:
    """Process uploaded voice memo: normalize audio, transcribe, restructure."""
    from saas.memo.processor import process_memo_file

    return process_memo_file(
        payload["file_path"],
        payload["episode_id"],
        payload["user_id"],
    )
