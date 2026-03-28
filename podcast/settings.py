"""
JSON-backed editorial settings for Mind the Gap podcast generation.

Settings are persisted to both a PostgreSQL table (primary, survives deploys)
and settings.json (fallback). Loaded fresh on every read so dashboard and
pipeline always agree.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

SETTINGS_FILE = Path(__file__).parent / "settings.json"

MALE_VOICES = [
    {"id": "xKhbyU7E3bC6T89Kn26c", "name": "Anand V3 (Custom)"},
    {"id": "VwBy5k1zgMTyXvcuAhyC", "name": "Anand V2 (Custom)"},
    {"id": "iP95p4xoKVk53GoZ742B", "name": "Chris — Charming, Down-to-Earth"},
    {"id": "TX3LPaxmHKxFdv7VOQHJ", "name": "Liam — Energetic, Social Media"},
    {"id": "nPczCjzI2devNBz1zQrb", "name": "Brian — Deep, Resonant, Comforting"},
    {"id": "bIHbv24MWmeRgasZH58o", "name": "Will — Relaxed Optimist"},
    {"id": "CwhRBWXzGAHq8TQ4Fs17", "name": "Roger — Laid-Back, Casual"},
    {"id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie — Deep, Confident, Energetic"},
]

FEMALE_VOICES = [
    {"id": "uYXf8XasLslADfZ2MB4u", "name": "Female Voice 1 (Custom)"},
    {"id": "VlaEyA6OJZwYWJNb9UPR", "name": "Gaju (Custom)"},
    {"id": "cgSgspJ2msm6clMCkdW9", "name": "Jessica — Playful, Bright, Warm"},
    {"id": "FGY2WhTYpPnrIDTdsKH5", "name": "Laura — Enthusiast, Quirky"},
    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah — Mature, Reassuring"},
    {"id": "hpp4J3VqNfWAUOO0d1Us", "name": "Bella — Professional, Bright"},
    {"id": "Xb7hH8MSUJpSbSDYk0k2", "name": "Alice — Clear, Engaging Educator"},
]

SCRIPT_MODELS = [
    {"id": "claude-opus", "name": "Claude Opus 4.6", "provider": "anthropic"},
    {"id": "gemini-3.1-pro", "name": "Gemini 3.1 Pro", "provider": "openrouter"},
    {"id": "gpt-5.4", "name": "GPT-5.4", "provider": "openrouter"},
    {"id": "deepseek-v3.2", "name": "DeepSeek V3.2", "provider": "openrouter"},
]

VALID_MODEL_IDS = {m["id"] for m in SCRIPT_MODELS}

DEFAULTS: dict = {
    "story_count": 3,
    "behavioral_concepts": 2,
    "spirituality_concepts": 1,
    "geo_toronto_pct": 25,
    "geo_canada_pct": 25,
    "geo_ai_tech_pct": 25,
    "geo_world_pct": 25,
    "voice_alex": MALE_VOICES[0]["id"],
    "voice_maya": FEMALE_VOICES[0]["id"],
    "audio_speed": 110,
    "tts_provider": "elevenlabs",
    "voice_direction_alex": "You are Alex, a charismatic and curious male podcast host. Speak naturally and conversationally — like you're genuinely excited to share ideas with your co-host and audience. Use warm energy, natural pauses, and vocal variety. Emphasize key points with subtle changes in pace and tone. Occasionally laugh or react authentically. Never sound like you're reading a script.",
    "voice_direction_maya": "You are Maya, an insightful and engaging female podcast host. Speak with natural warmth and intelligence — like you're having a fascinating conversation with a friend. Use expressive intonation, thoughtful pauses, and genuine reactions. Show enthusiasm when something is surprising or important. Be conversational and authentic, never robotic or flat.",
    "script_model": "claude-opus",
    "fallback_model": "gemini-3.1-pro",
}


def _db_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def _ensure_settings_table():
    url = _db_url()
    if not url:
        return
    try:
        import psycopg2
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS app_settings (
                        key TEXT PRIMARY KEY DEFAULT 'main',
                        data JSONB NOT NULL DEFAULT '{}'::jsonb,
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
            conn.commit()
        _table_ok = True
    except Exception as exc:
        _table_ok = False
        log.debug("Could not create app_settings table: %s", exc)
    return _table_ok


_table_ensured = False


def _load_from_db() -> dict | None:
    global _table_ensured
    url = _db_url()
    if not url:
        return None
    try:
        if not _table_ensured:
            if _ensure_settings_table():
                _table_ensured = True
        import psycopg2
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM app_settings WHERE key = 'main'")
                row = cur.fetchone()
                if row:
                    return row[0] if isinstance(row[0], dict) else json.loads(row[0])
    except Exception as exc:
        log.debug("Could not load settings from DB: %s", exc)
    return None


def _save_to_db(data: dict):
    global _table_ensured
    url = _db_url()
    if not url:
        return
    try:
        if not _table_ensured:
            if _ensure_settings_table():
                _table_ensured = True
        import psycopg2
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO app_settings (key, data, updated_at)
                    VALUES ('main', %s, NOW())
                    ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, updated_at = NOW()
                """, (json.dumps(data),))
            conn.commit()
    except Exception as exc:
        log.debug("Could not save settings to DB: %s", exc)


def load() -> dict:
    db_data = _load_from_db()
    if isinstance(db_data, dict) and db_data:
        return {**DEFAULTS, **db_data}
    if SETTINGS_FILE.exists():
        try:
            stored = json.loads(SETTINGS_FILE.read_text())
            merged = {**DEFAULTS, **stored}
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


BOUNDS = {
    "story_count": (1, 8),
    "behavioral_concepts": (0, 5),
    "spirituality_concepts": (0, 5),
    "geo_toronto_pct": (0, 100),
    "geo_canada_pct": (0, 100),
    "geo_ai_tech_pct": (0, 100),
    "geo_world_pct": (0, 100),
}


def save(updates: dict) -> dict:
    current = load()
    for key, val in updates.items():
        if key in BOUNDS and isinstance(val, (int, float)):
            lo, hi = BOUNDS[key]
            val = max(lo, min(hi, int(val)))
        if key in ("script_model", "fallback_model") and val not in VALID_MODEL_IDS:
            continue
        if key == "tts_provider" and val not in ("elevenlabs", "openai", "voxtral", "minimax", "11labs"):
            continue
        current[key] = val
    if current.get("fallback_model") == current.get("script_model"):
        fallback_options = [m for m in VALID_MODEL_IDS if m != current["script_model"]]
        current["fallback_model"] = fallback_options[0] if fallback_options else "gemini-3.1-pro"
    _save_to_db(current)
    try:
        SETTINGS_FILE.write_text(json.dumps(current, indent=2))
    except OSError as exc:
        log.debug("Could not write settings.json: %s", exc)
    return current
