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


def enqueue_job(db=None, job_type: str = "", payload: dict = None, delay_seconds: int = 0) -> str:
    """Enqueue a background job. Accepts an optional open db session or creates its own."""
    # Support both old signature (positional job_type) and new keyword-arg form with db
    if payload is None:
        payload = {}
    return _enqueue(job_type, payload, delay_seconds, db)


def _enqueue(job_type: str, payload: dict, delay_seconds: int = 0, external_db=None) -> str:
    """Enqueue a background job. Returns job_id."""
    from saas.db.models import Job, get_session
    from datetime import timedelta

    own_db = external_db is None
    db = get_session(os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db")) if own_db else external_db
    scheduled = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
    job = Job(
        id=str(uuid.uuid4()),
        type=job_type,
        payload=payload,
        status="queued",
        scheduled_at=scheduled,
    )
    db.add(job)
    db.commit()
    job_id = job.id
    if own_db:
        db.close()
    scheduler.add_job(
        _run_job,
        "date",
        run_date=scheduled,
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
    if job_type == "generate_episode":
        return _generate_episode(payload)
    if job_type == "deliver_webhook":
        return _deliver_webhook(payload)
    raise ValueError(f"Unknown job type: {job_type}")


def _process_memo(payload: dict) -> dict:
    """Process uploaded voice memo: normalize audio, transcribe, restructure."""
    from saas.memo.processor import process_memo_file

    return process_memo_file(
        payload["file_path"],
        payload["episode_id"],
        payload["user_id"],
    )


def _generate_episode(payload: dict) -> dict:
    """
    Generate a podcast episode via AI script writing + TTS.
    Updates the Episode row and fires episode.ready / episode.failed webhooks.
    """
    import os
    from saas.db.models import Episode, Podcast, get_session

    db = get_session(os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db"))
    episode_id = payload["episode_id"]
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        db.close()
        raise ValueError(f"Episode {episode_id} not found")

    podcast = db.query(Podcast).filter(Podcast.id == episode.podcast_id).first()

    try:
        episode.status = "generating"
        db.commit()

        # Import the existing generation pipeline
        from saas.models.generator import PodcastGenerator
        generator = PodcastGenerator()

        script = generator.generate_script(
            topic=payload["topic"],
            host_1_name=podcast.host_1_name if podcast else "Alex",
            host_2_name=podcast.host_2_name if podcast else "Maya",
            custom_notes=payload.get("custom_notes", ""),
        )
        episode.script = script
        episode.title = episode.title or script.get("title", episode.title)

        # Generate audio
        audio_result = generator.generate_audio(
            script=script,
            tts_provider=payload.get("tts_provider", podcast.tts_provider if podcast else "minimax"),
            host_1_voice=payload.get("host_1_voice") or (podcast.host_1_voice_id if podcast else None),
            host_2_voice=payload.get("host_2_voice") or (podcast.host_2_voice_id if podcast else None),
        )
        episode.audio_url = audio_result.get("audio_url")
        episode.audio_duration_seconds = audio_result.get("duration_seconds")
        episode.status = "ready"
        db.commit()

        # Fire webhook
        _fire_episode_event(db, payload["user_id"], "episode.ready", episode)
        result = {"status": "ready", "audio_url": episode.audio_url}

    except Exception as exc:
        log.exception("Episode generation failed for episode %s", episode_id)
        episode.status = "failed"
        episode.error_message = str(exc)
        db.commit()
        _fire_episode_event(db, payload["user_id"], "episode.failed", episode)
        raise
    finally:
        db.close()

    return result


def _fire_episode_event(db, user_id: int, event: str, episode) -> None:
    """Fire a webhook event for an episode status change."""
    try:
        from saas.api.webhooks import fire_event
        fire_event(db, user_id, event, {
            "episode_id": episode.id,
            "title": episode.title,
            "status": episode.status,
            "audio_url": getattr(episode, "audio_url", None),
            "error": getattr(episode, "error_message", None),
        })
    except Exception:
        log.warning("Failed to fire webhook event %s for episode %s", event, episode.id)


def _deliver_webhook(payload: dict) -> dict:
    """Deliver a single webhook event with retry-on-failure logic."""
    import os
    from saas.db.models import Webhook, get_session
    from saas.api.webhooks import deliver_webhook_sync

    db = get_session(os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db"))
    try:
        webhook = db.query(Webhook).filter(Webhook.id == payload["webhook_id"]).first()
        if not webhook or not webhook.is_active:
            return {"skipped": True}

        attempt = payload.get("attempt", 1)
        success = deliver_webhook_sync(
            db=db,
            webhook=webhook,
            event=payload["event"],
            data=payload["data"],
            attempt=attempt,
        )

        if not success and attempt < 3:
            # Schedule a retry with exponential backoff: 60s, 300s
            delay = 60 * (2 ** (attempt - 1))
            enqueue_job(
                job_type="deliver_webhook",
                payload={**payload, "attempt": attempt + 1},
                delay_seconds=delay,
            )
        return {"success": success, "attempt": attempt}
    finally:
        db.close()
