"""
Generates sound effects and jingles via the ElevenLabs Sound Effects API.

Used for:
  - Podcast intro/outro jingles (cached in podcast/assets/)
  - Ambient SFX clips mixed into episodes at scene transitions
"""
from __future__ import annotations

import logging
from pathlib import Path

from elevenlabs.client import ElevenLabs

import config

log = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

INTRO_PATH = ASSETS_DIR / "intro_jingle.mp3"
OUTRO_PATH = ASSETS_DIR / "outro_jingle.mp3"

INTRO_PROMPT = (
    "Upbeat modern podcast intro jingle, warm synth pad with gentle "
    "percussive rhythm, professional and inviting, energetic start"
)
OUTRO_PROMPT = (
    "Gentle podcast outro music, warm fading synth with soft chimes, "
    "reflective and calm, peaceful ending"
)


def _ensure_client() -> ElevenLabs:
    if not config.ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is not set.")
    return ElevenLabs(api_key=config.ELEVENLABS_API_KEY)


def generate_sfx(description: str, duration_seconds: float, output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = _ensure_client()
    log.info("Generating SFX: '%s' (%.1fs) -> %s", description, duration_seconds, output_path)

    result = client.text_to_sound_effects.convert(
        text=description,
        duration_seconds=min(duration_seconds, 22.0),
    )

    audio_bytes = b"".join(result)
    output_path.write_bytes(audio_bytes)
    log.info("SFX saved: %s (%.1f KB)", output_path.name, len(audio_bytes) / 1024)
    return output_path


def generate_intro_jingle(force: bool = False) -> Path:
    if INTRO_PATH.exists() and not force:
        log.info("Intro jingle already cached at %s", INTRO_PATH)
        return INTRO_PATH
    log.info("Generating intro jingle...")
    return generate_sfx(INTRO_PROMPT, 8.0, INTRO_PATH)


def generate_outro_jingle(force: bool = False) -> Path:
    if OUTRO_PATH.exists() and not force:
        log.info("Outro jingle already cached at %s", OUTRO_PATH)
        return OUTRO_PATH
    log.info("Generating outro jingle...")
    return generate_sfx(OUTRO_PROMPT, 6.0, OUTRO_PATH)
