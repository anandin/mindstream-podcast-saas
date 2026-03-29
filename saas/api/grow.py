"""
Grow Layer API — Discoverability features for CastAPI / ScriptFlow episodes.

Endpoints:
  POST /api/v1/episodes/{id}/seo-title     Generate SEO-optimised episode title
  POST /api/v1/episodes/{id}/show-notes    Generate structured show notes (markdown)
  POST /api/v1/episodes/{id}/audiogram     Queue audiogram generation (stub)
  GET  /api/v1/episodes/{id}/grow          All grow metadata for an episode

AI calls go through OpenRouter (Gemini 2.5 Pro) — same model as the rest of the pipeline.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from saas.api.main import get_db, get_current_user
from saas.db.models import Episode, Podcast, User

router = APIRouter(prefix="/api/v1/episodes", tags=["grow"])

# ── LLM helper ────────────────────────────────────────────────────────────────

def _llm(system: str, user_prompt: str, max_tokens: int = 512) -> str:
    """
    Call OpenRouter (Gemini 2.5 Pro) for a single-shot completion.
    Falls back gracefully if env vars are missing.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    payload = {
        "model": "google/gemini-2.5-pro-preview",
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://mindstream.fm",
            "X-Title": "MindStream Grow Layer",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


# ── Auth helper ────────────────────────────────────────────────────────────────

def _get_episode(episode_id: int, user: User, db: Session) -> Episode:
    ep = (
        db.query(Episode)
        .join(Podcast)
        .filter(Episode.id == episode_id, Podcast.user_id == user.id)
        .first()
    )
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    return ep


# ── Pydantic ───────────────────────────────────────────────────────────────────

class GrowMeta(BaseModel):
    episode_id: int
    title: Optional[str]
    seo_title: Optional[str]
    show_notes: Optional[str]
    audiogram_status: str
    audiogram_url: Optional[str]


# ── GET grow metadata ─────────────────────────────────────────────────────────

@router.get("/{episode_id}/grow", response_model=GrowMeta)
async def get_grow_meta(
    episode_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all Grow Layer metadata for an episode."""
    ep = _get_episode(episode_id, current_user, db)
    return GrowMeta(
        episode_id=ep.id,
        title=ep.title,
        seo_title=ep.seo_title,
        show_notes=ep.show_notes,
        audiogram_status=ep.audiogram_status or "none",
        audiogram_url=ep.audiogram_url,
    )


# ── SEO title ─────────────────────────────────────────────────────────────────

@router.post("/{episode_id}/seo-title")
async def generate_seo_title(
    episode_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Use Gemini 2.5 Pro to generate an SEO-optimised episode title.
    Rewrites the raw title to be search-friendly (60-70 chars, question-
    or benefit-driven, no clickbait).
    """
    ep = _get_episode(episode_id, current_user, db)

    source = ep.title or ""
    if ep.description:
        source += "\n\nDescription: " + ep.description[:300]
    if ep.transcript:
        source += "\n\nTranscript excerpt: " + ep.transcript[:500]

    if not source.strip():
        raise HTTPException(status_code=400, detail="Episode has no content to generate a title from")

    system = (
        "You are an SEO copywriter for a podcast platform. "
        "Output ONLY the new title — no explanation, no quotes, no markdown."
    )
    prompt = (
        f"Rewrite this podcast episode title to be SEO-optimised for search engines. "
        f"Keep it under 70 characters, make it benefit-driven or question-based, "
        f"no clickbait. Original title and context:\n\n{source}"
    )

    try:
        seo_title = _llm(system, prompt, max_tokens=80)
        # Strip any accidental quotes
        seo_title = seo_title.strip('"\'').strip()
        ep.seo_title = seo_title[:500]
        ep.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"episode_id": ep.id, "seo_title": ep.seo_title}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")


# ── Show notes ────────────────────────────────────────────────────────────────

@router.post("/{episode_id}/show-notes")
async def generate_show_notes(
    episode_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate structured show notes as markdown:
      - Episode summary (2-3 sentences)
      - Key takeaways (3-5 bullet points)
      - Notable quotes (if transcript available)
      - Suggested tags (5 keywords)
    """
    ep = _get_episode(episode_id, current_user, db)

    content_parts = []
    if ep.title:
        content_parts.append(f"Title: {ep.title}")
    if ep.description:
        content_parts.append(f"Description: {ep.description[:500]}")
    if ep.transcript:
        content_parts.append(f"Transcript excerpt:\n{ep.transcript[:2000]}")
    elif ep.script:
        # Extract plain text from script JSON
        script_text = ""
        if isinstance(ep.script, list):
            script_text = " ".join(
                seg.get("text", "") for seg in ep.script if isinstance(seg, dict)
            )
        elif isinstance(ep.script, dict):
            script_text = ep.script.get("transcript", "")
        if script_text:
            content_parts.append(f"Script excerpt:\n{script_text[:2000]}")

    if not content_parts:
        raise HTTPException(status_code=400, detail="Episode has no content for show notes")

    source = "\n\n".join(content_parts)

    system = (
        "You are a podcast producer writing show notes for a podcast directory listing. "
        "Format your response in clean markdown with exactly these four sections: "
        "## Summary, ## Key Takeaways, ## Notable Quotes, ## Tags. "
        "Output only the markdown — no preamble."
    )
    prompt = f"Write show notes for this podcast episode:\n\n{source}"

    try:
        show_notes = _llm(system, prompt, max_tokens=600)
        ep.show_notes = show_notes
        ep.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"episode_id": ep.id, "show_notes": ep.show_notes}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")


# ── Audiogram (stub) ──────────────────────────────────────────────────────────

@router.post("/{episode_id}/audiogram")
async def queue_audiogram(
    episode_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Queue audiogram generation for a podcast episode.

    An audiogram is a short social-media video (60s): waveform animation
    + episode cover image + subtitle captions.

    Current status: stub — queues a job but does not yet render.
    The job runner will be wired to a real renderer (e.g. FFmpeg + Pillow)
    in a future release. Returns the job ID for polling.
    """
    ep = _get_episode(episode_id, current_user, db)

    if ep.status not in ("ready", "published"):
        raise HTTPException(
            status_code=400,
            detail=f"Episode must be in 'ready' or 'published' status to generate audiogram (current: {ep.status})"
        )
    if not ep.audio_url:
        raise HTTPException(status_code=400, detail="Episode has no audio URL")

    # Enqueue the job (grow_audiogram type is a stub in runner.py)
    from saas.jobs.runner import enqueue_job
    from saas.db.models import get_session

    db2 = get_session(os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db"))
    job_id = enqueue_job(
        db=db2,
        job_type="grow_audiogram",
        payload={
            "episode_id": ep.id,
            "audio_url": ep.audio_url,
            "title": ep.seo_title or ep.title or "",
            "duration_seconds": ep.audio_duration_seconds or 60,
        },
    )
    db2.close()

    ep.audiogram_status = "queued"
    ep.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "episode_id": ep.id,
        "audiogram_status": "queued",
        "job_id": job_id,
        "message": "Audiogram generation queued. This feature renders in a future release.",
    }
