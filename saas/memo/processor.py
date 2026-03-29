"""Memo.fm audio processing and AI restructuring pipeline."""
import os
import logging
import json
from pathlib import Path

log = logging.getLogger(__name__)


def process_memo_file(file_path: str, episode_id: int, user_id: int) -> dict:
    """Full pipeline: normalize -> transcribe -> restructure -> update episode."""
    # Step 1: Normalize audio
    normalized_path = normalize_audio(file_path)
    duration = get_duration(normalized_path)

    # Step 2: Transcribe
    transcript = transcribe_audio(normalized_path)

    # Step 3: AI restructure into episode
    structured = restructure_transcript(transcript)

    # Step 4: Update episode in DB
    update_episode(episode_id, transcript, structured, normalized_path, duration)

    return {
        "episode_id": episode_id,
        "duration": duration,
        "transcript_length": len(transcript),
    }


def normalize_audio(input_path: str) -> str:
    """Normalize volume, trim silence, noise reduction."""
    from pydub import AudioSegment
    from pydub.effects import normalize

    audio = AudioSegment.from_file(input_path)
    audio = normalize(audio)
    # Trim silence from start/end
    audio = audio.strip_silence(silence_len=1000, silence_thresh=-40, padding=200)

    out_path = input_path.rsplit(".", 1)[0] + "_normalized.mp3"
    audio.export(out_path, format="mp3", bitrate="128k")
    return out_path


def get_duration(audio_path: str) -> float:
    """Return duration of audio file in seconds."""
    from pydub import AudioSegment

    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0


def transcribe_audio(audio_path: str) -> str:
    """Transcribe using AssemblyAI if key available, else return placeholder."""
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if api_key:
        return _transcribe_assemblyai(audio_path, api_key)
    # Fallback: return filename as placeholder for testing
    return f"[Transcription pending — audio at {audio_path}]"


def _transcribe_assemblyai(audio_path: str, api_key: str) -> str:
    """Submit audio to AssemblyAI and poll for the completed transcript."""
    import requests
    import time

    headers = {"authorization": api_key, "content-type": "application/json"}

    # Upload audio file
    with open(audio_path, "rb") as f:
        upload = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers={"authorization": api_key},
            data=f,
        )
    audio_url = upload.json()["upload_url"]

    # Submit transcription job
    resp = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json={"audio_url": audio_url},
    )
    tid = resp.json()["id"]

    # Poll for completion
    for _ in range(60):
        time.sleep(3)
        r = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{tid}",
            headers=headers,
        )
        s = r.json()["status"]
        if s == "completed":
            return r.json()["text"]
        if s == "error":
            raise RuntimeError(r.json().get("error", "Transcription failed"))

    raise TimeoutError("Transcription timed out")


def restructure_transcript(transcript: str) -> dict:
    """Use Gemini via OpenRouter to restructure transcript into episode structure."""
    import requests

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "title": "Untitled Episode",
            "intro": transcript[:200],
            "points": [],
            "outro": "",
        }

    prompt = f"""You are a podcast producer. Restructure this voice memo transcript into a polished episode.

Transcript:
{transcript[:3000]}

Return JSON with these exact fields:
{{
  "title": "compelling episode title (max 60 chars)",
  "intro": "hook intro paragraph (2-3 sentences that grab attention)",
  "main_points": [
    {{"heading": "point 1 title", "content": "expanded content for this point"}},
    {{"heading": "point 2 title", "content": "expanded content"}},
    {{"heading": "point 3 title", "content": "expanded content"}}
  ],
  "outro": "closing call-to-action paragraph",
  "show_notes_summary": "2-sentence summary for show notes"
}}"""

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "google/gemini-2.5-pro-preview",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def update_episode(
    episode_id: int,
    transcript: str,
    structured: dict,
    audio_path: str,
    duration: float,
) -> None:
    """Persist transcript, structured content, and audio info to the episode record."""
    from saas.db.models import Episode, get_session

    db = get_session(os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db"))
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if ep:
        ep.transcript = transcript
        ep.title = structured.get("title", "Untitled Episode")
        ep.description = structured.get("show_notes_summary", "")
        ep.script = structured
        ep.audio_url = audio_path
        ep.audio_duration_seconds = duration
        ep.status = "ready"
        db.commit()
    db.close()
