"""Memo.fm API routes — voice memo upload and RSS feed."""
import os
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from saas.db.models import User, Podcast, Episode, get_session
from saas.api.main import get_db, get_current_user

router = APIRouter(prefix="/api/v1/memo", tags=["memo"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads/memo"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_memo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a voice memo. Returns episode_id and job_id."""
    # Validate file type
    allowed = {"audio/webm", "audio/mp4", "audio/mpeg", "audio/wav", "audio/ogg"}
    if file.content_type not in allowed:
        raise HTTPException(400, f"Unsupported audio type: {file.content_type}")

    # Save uploaded file
    file_id = str(uuid.uuid4())
    suffix = Path(file.filename or "memo.webm").suffix or ".webm"
    file_path = UPLOAD_DIR / f"{file_id}{suffix}"
    with file_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Get or create default memo podcast for user
    podcast = db.query(Podcast).filter(
        Podcast.user_id == current_user.id,
        Podcast.title == "My Memo.fm Feed",
    ).first()
    if not podcast:
        podcast = Podcast(
            user_id=current_user.id,
            title="My Memo.fm Feed",
            description=f"{current_user.name or current_user.email}'s voice memos",
            tts_provider="minimax",
        )
        db.add(podcast)
        db.commit()
        db.refresh(podcast)

    # Create episode record
    episode = Episode(
        podcast_id=podcast.id,
        date=datetime.now(timezone.utc),
        title="Processing...",
        status="processing",
        audio_url=str(file_path),
    )
    db.add(episode)
    db.commit()
    db.refresh(episode)

    # Enqueue processing job
    from saas.jobs.runner import enqueue_job

    job_id = enqueue_job(
        "process_memo",
        {
            "file_path": str(file_path),
            "episode_id": episode.id,
            "user_id": current_user.id,
        },
    )

    return {"episode_id": episode.id, "job_id": job_id, "status": "processing"}


@router.get("/episode/{episode_id}/status")
async def episode_status(
    episode_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll episode processing status."""
    ep = (
        db.query(Episode)
        .join(Podcast)
        .filter(
            Episode.id == episode_id,
            Podcast.user_id == current_user.id,
        )
        .first()
    )
    if not ep:
        raise HTTPException(404, "Episode not found")
    return {
        "episode_id": ep.id,
        "status": ep.status,
        "title": ep.title,
        "duration_seconds": ep.audio_duration_seconds,
        "audio_url": ep.audio_url if ep.status == "ready" else None,
    }


@router.get("/feed/{token}", response_class=Response)
async def rss_feed(token: str, db: Session = Depends(get_db)):
    """Private RSS feed endpoint."""
    from saas.memo.rss import generate_rss

    podcast = (
        db.query(Podcast)
        .filter(Podcast.transistor_show_id == f"rss_{token}")
        .first()
    )
    if not podcast:
        raise HTTPException(404, "Feed not found")
    episodes = (
        db.query(Episode)
        .filter(
            Episode.podcast_id == podcast.id,
            Episode.status == "ready",
        )
        .order_by(Episode.date.desc())
        .all()
    )
    rss_xml = generate_rss(podcast, episodes, token)
    return Response(content=rss_xml, media_type="application/rss+xml")
