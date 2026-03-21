"""
Episode archive & metadata store — PostgreSQL-backed.

Stores episode metadata and archives all output files for later analysis.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import date, datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

log = logging.getLogger(__name__)

HERE = Path(__file__).parent
OUTPUT_DIR = HERE / "output"
ARCHIVE_DIR = HERE / "archive"
ARCHIVE_DIR.mkdir(exist_ok=True)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS episodes (
    id SERIAL PRIMARY KEY,
    episode_date DATE NOT NULL UNIQUE,
    title TEXT,
    description TEXT,
    story_count INT,
    target_words INT,
    actual_words INT,
    actual_chars INT,
    duration_minutes FLOAT,
    anthropic_input_tokens INT,
    anthropic_output_tokens INT,
    anthropic_thinking_tokens INT,
    elevenlabs_credits INT,
    estimated_cost_usd FLOAT,
    transistor_episode_id TEXT,
    share_url TEXT,
    script_path TEXT,
    script_content JSONB,
    transcript_path TEXT,
    audio_path TEXT,
    description_path TEXT,
    file_size_bytes BIGINT,
    status TEXT DEFAULT 'generated',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ
)
"""


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _ensure_table():
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_CREATE_TABLE)
                cur.execute(
                    "ALTER TABLE episodes ADD COLUMN IF NOT EXISTS script_content JSONB"
                )
            conn.commit()
    except Exception as exc:
        log.warning("Could not ensure episodes table: %s", exc)


_ensure_table()


def _backfill_script_content():
    """One-time migration: populate script_content from archive files for any
    episodes that have a script_path but no script_content yet."""
    try:
        with _conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT episode_date, script_path FROM episodes "
                    "WHERE script_content IS NULL AND script_path IS NOT NULL"
                )
                rows = cur.fetchall()
            if not rows:
                return
            log.info("Back-filling script_content for %d episode(s)…", len(rows))
            for row in rows:
                stem = str(row["episode_date"])
                candidates = [
                    Path(row["script_path"]),
                    ARCHIVE_DIR / stem / f"{stem}_script.json",
                    OUTPUT_DIR / f"{stem}_script.json",
                ]
                for path in candidates:
                    if path.exists():
                        try:
                            content = json.loads(path.read_text())
                            with conn.cursor() as cur:
                                cur.execute(
                                    "UPDATE episodes SET script_content = %s WHERE episode_date = %s",
                                    (json.dumps(content), row["episode_date"]),
                                )
                            conn.commit()
                            log.info("  Back-filled script_content for %s from %s", stem, path)
                        except Exception as e:
                            log.warning("  Failed to back-fill %s: %s", stem, e)
                        break
                else:
                    log.warning("  No script file found for %s — skipping back-fill", stem)
    except Exception as exc:
        log.warning("Script content back-fill failed: %s", exc)


_backfill_script_content()


def archive_episode(
    episode_date: date,
    title: str | None = None,
    description: str | None = None,
    transistor_id: str | None = None,
    share_url: str | None = None,
) -> dict:
    stem = episode_date.strftime("%Y-%m-%d")
    day_dir = ARCHIVE_DIR / stem
    day_dir.mkdir(parents=True, exist_ok=True)

    file_map = {}
    for suffix in ["script.json", "transcript.txt", "episode.mp3", "description.txt"]:
        src = OUTPUT_DIR / f"{stem}_{suffix}"
        if src.exists():
            dst = day_dir / f"{stem}_{suffix}"
            shutil.copy2(src, dst)
            file_map[suffix.split(".")[0]] = str(dst)
            log.info("Archived %s → %s", src.name, dst)

    script_data = {}
    script_json_content = None
    script_path = OUTPUT_DIR / f"{stem}_script.json"
    if script_path.exists():
        try:
            raw = script_path.read_text()
            script = json.loads(raw)
            script_json_content = script
            dialogue_turns = [t for t in script if t.get("speaker", "").upper() in ("ALEX", "MAYA")]
            script_data["actual_words"] = sum(len(t["text"].split()) for t in dialogue_turns)
            script_data["actual_chars"] = sum(len(t["text"]) for t in dialogue_turns)
            script_data["story_count"] = _count_stories(script)
        except Exception as e:
            log.warning("Could not parse script for stats: %s", e)

    if not title:
        desc_path = OUTPUT_DIR / f"{stem}_description.txt"
        if desc_path.exists():
            lines = desc_path.read_text().strip().splitlines()
            if lines:
                title = lines[0]

    audio_path = OUTPUT_DIR / f"{stem}_episode.mp3"
    file_size = audio_path.stat().st_size if audio_path.exists() else 0

    target_words = min(1550 + (script_data.get("story_count", 1) - 1) * 220, 3100)
    actual_words = script_data.get("actual_words", 0)
    actual_chars = script_data.get("actual_chars", 0)
    duration = round(actual_words / 155, 1) if actual_words else 0

    input_tokens = 4000 + script_data.get("story_count", 1) * 500
    thinking_tokens = 5000 + script_data.get("story_count", 1) * 800
    output_tokens = round(actual_words * 1.35) if actual_words else 0
    el_credits = actual_chars + script_data.get("story_count", 1) * 400

    anthropic_cost = (input_tokens + 200) / 1e6 * 15 + thinking_tokens / 1e6 * 15 + (output_tokens + 50) / 1e6 * 75
    el_cost = el_credits * 0.00022
    hosting_cost = 7.0 / 30
    total_cost = anthropic_cost + el_cost + hosting_cost

    row = {
        "episode_date": episode_date,
        "title": title,
        "description": description,
        "story_count": script_data.get("story_count"),
        "target_words": target_words,
        "actual_words": actual_words or None,
        "actual_chars": actual_chars or None,
        "duration_minutes": duration or None,
        "anthropic_input_tokens": input_tokens,
        "anthropic_output_tokens": output_tokens,
        "anthropic_thinking_tokens": thinking_tokens,
        "elevenlabs_credits": el_credits,
        "estimated_cost_usd": round(total_cost, 4),
        "transistor_episode_id": transistor_id,
        "share_url": share_url,
        "script_path": file_map.get("script"),
        "script_content": json.dumps(script_json_content) if script_json_content is not None else None,
        "transcript_path": file_map.get("transcript"),
        "audio_path": file_map.get("episode"),
        "description_path": file_map.get("description"),
        "file_size_bytes": file_size,
        "status": "published" if transistor_id else "generated",
        "published_at": datetime.utcnow() if transistor_id else None,
    }

    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO episodes (
                    episode_date, title, description, story_count, target_words,
                    actual_words, actual_chars, duration_minutes,
                    anthropic_input_tokens, anthropic_output_tokens, anthropic_thinking_tokens,
                    elevenlabs_credits, estimated_cost_usd,
                    transistor_episode_id, share_url,
                    script_path, script_content, transcript_path, audio_path, description_path,
                    file_size_bytes, status, published_at
                ) VALUES (
                    %(episode_date)s, %(title)s, %(description)s, %(story_count)s, %(target_words)s,
                    %(actual_words)s, %(actual_chars)s, %(duration_minutes)s,
                    %(anthropic_input_tokens)s, %(anthropic_output_tokens)s, %(anthropic_thinking_tokens)s,
                    %(elevenlabs_credits)s, %(estimated_cost_usd)s,
                    %(transistor_episode_id)s, %(share_url)s,
                    %(script_path)s, %(script_content)s::jsonb, %(transcript_path)s, %(audio_path)s, %(description_path)s,
                    %(file_size_bytes)s, %(status)s, %(published_at)s
                )
                ON CONFLICT (episode_date) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = COALESCE(EXCLUDED.description, episodes.description),
                    story_count = COALESCE(EXCLUDED.story_count, episodes.story_count),
                    target_words = EXCLUDED.target_words,
                    actual_words = COALESCE(EXCLUDED.actual_words, episodes.actual_words),
                    actual_chars = COALESCE(EXCLUDED.actual_chars, episodes.actual_chars),
                    duration_minutes = COALESCE(EXCLUDED.duration_minutes, episodes.duration_minutes),
                    anthropic_input_tokens = EXCLUDED.anthropic_input_tokens,
                    anthropic_output_tokens = EXCLUDED.anthropic_output_tokens,
                    anthropic_thinking_tokens = EXCLUDED.anthropic_thinking_tokens,
                    elevenlabs_credits = EXCLUDED.elevenlabs_credits,
                    estimated_cost_usd = EXCLUDED.estimated_cost_usd,
                    transistor_episode_id = COALESCE(EXCLUDED.transistor_episode_id, episodes.transistor_episode_id),
                    share_url = COALESCE(EXCLUDED.share_url, episodes.share_url),
                    script_path = COALESCE(EXCLUDED.script_path, episodes.script_path),
                    script_content = COALESCE(EXCLUDED.script_content, episodes.script_content),
                    transcript_path = COALESCE(EXCLUDED.transcript_path, episodes.transcript_path),
                    audio_path = COALESCE(EXCLUDED.audio_path, episodes.audio_path),
                    description_path = COALESCE(EXCLUDED.description_path, episodes.description_path),
                    file_size_bytes = COALESCE(EXCLUDED.file_size_bytes, episodes.file_size_bytes),
                    status = EXCLUDED.status,
                    published_at = COALESCE(EXCLUDED.published_at, episodes.published_at)
            """, row)
            conn.commit()

    log.info("Episode %s archived to DB (status=%s, cost=$%.2f)", stem, row["status"], total_cost)
    return row


def _count_stories(script: list[dict]) -> int:
    count = 0
    for t in script:
        text = t.get("text", "").lower()
        if any(marker in text for marker in ["story number", "first story", "next story", "our next", "let's move", "shifting gears", "moving on to"]):
            count += 1
    from settings import load as load_settings
    settings = load_settings()
    return max(count, settings.get("story_count", 1))


def get_all_episodes() -> list[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM episodes ORDER BY episode_date DESC")
            return [dict(r) for r in cur.fetchall()]


def get_episode(episode_date: date) -> dict | None:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM episodes WHERE episode_date = %s", (episode_date,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_summary_stats() -> dict:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total_episodes,
                    COUNT(*) FILTER (WHERE status = 'published') as published_count,
                    ROUND(AVG(actual_words)::numeric, 0) as avg_words,
                    ROUND(AVG(duration_minutes)::numeric, 1) as avg_duration_min,
                    ROUND(AVG(estimated_cost_usd)::numeric, 2) as avg_cost_usd,
                    ROUND(SUM(estimated_cost_usd)::numeric, 2) as total_cost_usd,
                    ROUND(AVG(elevenlabs_credits)::numeric, 0) as avg_el_credits,
                    ROUND(SUM(file_size_bytes)::numeric / 1048576, 1) as total_size_mb,
                    MIN(episode_date) as first_episode,
                    MAX(episode_date) as latest_episode
                FROM episodes
            """)
            return dict(cur.fetchone())
