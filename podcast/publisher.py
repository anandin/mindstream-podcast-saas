"""
Publishes finished podcast episodes to Transistor.fm.

Transistor.fm upload flow
─────────────────────────
1. POST /v1/episodes                    → create episode (draft)
2. GET  /v1/episodes/authorize_upload   → get pre-signed S3 URL + audio_url
3. PUT  <s3_url>                        → upload the MP3 binary
4. PATCH /v1/episodes/{id}              → link audio_url to episode
5. PATCH /v1/episodes/{id}/publish      → set status=published (form data)
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import requests

import config

log = logging.getLogger(__name__)

HEADERS = {
    "x-api-key": config.TRANSISTOR_API_KEY,
    "Content-Type": "application/json",
}


def _api(method: str, path: str, **kwargs) -> dict:
    """Thin wrapper around Transistor.fm API calls."""
    url = f"{config.TRANSISTOR_BASE_URL}{path}"
    resp = requests.request(method, url, headers=HEADERS, timeout=30, **kwargs)
    if not resp.ok:
        raise RuntimeError(
            f"Transistor.fm API error {resp.status_code} on {method} {path}: {resp.text[:400]}"
        )
    return resp.json()


def create_episode(
    title: str,
    description: str,
    episode_date: date | None = None,
) -> str:
    """
    Create a draft episode on Transistor.fm and return its episode ID.
    """
    payload = {
        "episode": {
            "show_id": config.TRANSISTOR_SHOW_ID,
            "title": title,
            "summary": description[:500],  # Transistor summary limit
            "description": description,
            "type": "full",
        }
    }

    log.info("Creating episode on Transistor.fm: '%s'", title)
    data = _api("POST", "/episodes", json=payload)
    episode_id = data["data"]["id"]
    log.info("Episode created — ID: %s", episode_id)
    return episode_id


def upload_audio(episode_id: str, audio_path: Path) -> None:
    """
    Fetch a pre-signed upload URL from Transistor and PUT the MP3 there.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Step 1: get a pre-signed S3 URL (collection-level endpoint)
    log.info("Authorising audio upload for episode %s…", episode_id)
    auth = _api(
        "GET",
        "/episodes/authorize_upload",
        params={"filename": audio_path.name},
    )
    upload_url = auth["data"]["attributes"]["upload_url"]
    audio_url = auth["data"]["attributes"]["audio_url"]
    content_type = auth["data"]["attributes"].get("content_type", "audio/mpeg")

    # Step 2: PUT the MP3 to S3
    log.info("Uploading %s (%.1f MB) to S3…", audio_path.name, audio_path.stat().st_size / 1e6)
    with open(audio_path, "rb") as f:
        put_resp = requests.put(
            upload_url,
            data=f,
            headers={"Content-Type": content_type},
            timeout=300,
        )
    put_resp.raise_for_status()
    log.info("Audio uploaded successfully.")

    # Step 3: link the uploaded audio to the episode
    _api(
        "PATCH",
        f"/episodes/{episode_id}",
        json={"episode": {"audio_url": audio_url}},
    )


def publish_episode(episode_id: str, episode_date: date | None = None) -> str:
    """
    Publish the episode via the dedicated /publish endpoint.
    Returns the episode's public share URL.
    """
    url = f"{config.TRANSISTOR_BASE_URL}/episodes/{episode_id}/publish"
    form = {"episode[status]": "published"}

    resp = requests.patch(
        url,
        headers={"x-api-key": config.TRANSISTOR_API_KEY},
        data=form,
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(
            f"Transistor.fm publish error {resp.status_code}: {resp.text[:400]}"
        )
    data = resp.json()
    share_url = data["data"]["attributes"].get("share_url", "")
    log.info("Episode published! URL: %s", share_url)
    return share_url


def publish_full_episode(
    title: str,
    description: str,
    audio_path: Path,
    episode_date: date | None = None,
) -> dict[str, str]:
    """
    End-to-end: create → upload → publish. Returns episode metadata.
    """
    episode_id = create_episode(title, description, episode_date)
    upload_audio(episode_id, audio_path)
    share_url = publish_episode(episode_id, episode_date)
    return {"episode_id": episode_id, "share_url": share_url}
