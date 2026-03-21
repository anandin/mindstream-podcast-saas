"""
Story Memory — tracks what topics/stories have been covered across episodes.

Prevents the podcast from repeating old news and enables Sunday weekly recaps.
SQLite version for local development (PostgreSQL for production).
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path

log = logging.getLogger(__name__)

# Use SQLite for local dev, PostgreSQL for production
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./story_memory.db")
IS_SQLITE = DATABASE_URL.startswith("sqlite://")

if IS_SQLITE:
    # Extract path from sqlite:///path
    DB_PATH = DATABASE_URL.replace("sqlite:///", "")
else:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        psycopg2 = None
        log.warning("psycopg2 not available, falling back to SQLite")

_CREATE_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS story_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_date DATE NOT NULL,
    topic_category TEXT NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_entities TEXT DEFAULT '[]',
    is_continuation BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(episode_date, headline)
);
CREATE INDEX IF NOT EXISTS idx_story_memory_date ON story_memory (episode_date DESC);
"""

def _conn():
    if IS_SQLITE:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        return psycopg2.connect(DATABASE_URL)

def _ensure_table():
    try:
        if IS_SQLITE:
            conn = sqlite3.connect(DB_PATH)
            conn.executescript(_CREATE_TABLE_SQLITE)
            conn.close()
            log.debug("story_memory SQLite table ready")
        else:
            # PostgreSQL path - skip for now
            log.debug("PostgreSQL path - table creation skipped")
    except Exception as exc:
        log.warning("Could not create story_memory table: %s", exc)

_ensure_table()

def store_stories(episode_date: date, stories: list[dict]) -> int:
    if not stories:
        return 0
    
    count = 0
    try:
        if IS_SQLITE:
            conn = sqlite3.connect(DB_PATH)
            for s in stories:
                try:
                    conn.execute(
                        """INSERT OR REPLACE INTO story_memory 
                           (episode_date, topic_category, headline, summary, key_entities, is_continuation)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            episode_date.isoformat(),
                            s.get("topic_category", "general"),
                            s.get("headline", ""),
                            s.get("summary", ""),
                            json.dumps(s.get("key_entities", [])),
                            s.get("is_continuation", False),
                        )
                    )
                    count += 1
                except Exception as e:
                    log.warning("Failed to store story: %s", e)
            conn.commit()
            conn.close()
        log.info("Stored %d story memories for %s", count, episode_date)
        return count
    except Exception as exc:
        log.warning("Failed to store stories: %s", exc)
        return 0

def get_recent_stories(days: int = 7, before_date: date | None = None) -> list[dict]:
    ref = before_date or date.today()
    cutoff = ref - timedelta(days=days)
    
    try:
        if IS_SQLITE:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                """SELECT episode_date, topic_category, headline, summary, key_entities, is_continuation
                   FROM story_memory
                   WHERE episode_date >= ? AND episode_date < ?
                   ORDER BY episode_date DESC, id ASC""",
                (cutoff.isoformat(), ref.isoformat())
            )
            rows = []
            for row in cur.fetchall():
                d = dict(row)
                d['key_entities'] = json.loads(d.get('key_entities', '[]'))
                rows.append(d)
            conn.close()
            return rows
    except Exception as exc:
        log.warning("Failed to get recent stories: %s", exc)
        return []

def get_covered_headlines(days: int = 6) -> list[str]:
    """Get list of headlines from recent episodes for upstream deduplication."""
    stories = get_recent_stories(days=days)
    return [s["headline"] for s in stories if s.get("headline")]

def format_recent_for_prompt(days: int = 6) -> str:
    """Format recent stories for injection into script prompt."""
    stories = get_recent_stories(days=days)
    if not stories:
        return ""
    lines = ["Recently covered stories (DO NOT lead with these topics):"]
    for s in stories[:10]:
        lines.append(f"- [{s['topic_category']}] {s['headline']}")
    return "\n".join(lines)

def format_week_for_recap() -> str:
    """Format full week for Sunday recap episode."""
    stories = get_recent_stories(days=7)
    if not stories:
        return ""
    lines = ["Stories covered this week:"]
    for s in stories:
        lines.append(f"- {s['headline']}: {s['summary'][:100]}...")
    return "\n".join(lines)

def prune_old_stories(days: int = 90) -> int:
    """Remove stories older than N days."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    try:
        if IS_SQLITE:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.execute("DELETE FROM story_memory WHERE episode_date < ?", (cutoff,))
            deleted = cur.rowcount
            conn.commit()
            conn.close()
            log.info("Pruned %d old stories", deleted)
            return deleted
    except Exception as exc:
        log.warning("Failed to prune stories: %s", exc)
        return 0

def extract_story_summaries(script_text: str) -> list[dict]:
    """Extract story summaries from generated script using LLM."""
    # This would need LLM integration - stub for now
    return []
