"""
Story Memory — tracks what topics/stories have been covered across episodes.

Prevents the podcast from repeating old news and enables Sunday weekly recaps.
Uses PostgreSQL for persistent storage with automatic pruning for long-term sustainability.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

log = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS story_memory (
    id SERIAL PRIMARY KEY,
    episode_date DATE NOT NULL,
    topic_category TEXT NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_entities TEXT[] DEFAULT '{}',
    is_continuation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_story_memory_date ON story_memory (episode_date DESC);
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_story_memory_date_headline'
    ) THEN
        ALTER TABLE story_memory ADD CONSTRAINT uq_story_memory_date_headline
            UNIQUE (episode_date, headline);
    END IF;
END $$;
"""


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _ensure_table():
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_CREATE_TABLE)
            conn.commit()
        log.debug("story_memory table ready")
    except Exception as exc:
        log.warning("Could not create story_memory table: %s", exc)


_ensure_table()


def store_stories(episode_date: date, stories: list[dict]) -> int:
    if not stories:
        return 0
    sql = """
        INSERT INTO story_memory (episode_date, topic_category, headline, summary, key_entities, is_continuation)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (episode_date, headline) DO UPDATE SET
            summary = EXCLUDED.summary,
            key_entities = EXCLUDED.key_entities,
            is_continuation = EXCLUDED.is_continuation
    """
    count = 0
    with _conn() as conn:
        with conn.cursor() as cur:
            for s in stories:
                cur.execute(sql, (
                    episode_date,
                    s.get("topic_category", "general"),
                    s.get("headline", ""),
                    s.get("summary", ""),
                    s.get("key_entities", []),
                    s.get("is_continuation", False),
                ))
                count += 1
        conn.commit()
    log.info("Stored %d story memories for %s", count, episode_date)
    return count


def get_recent_stories(days: int = 7, before_date: date | None = None) -> list[dict]:
    ref = before_date or date.today()
    cutoff = ref - timedelta(days=days)
    sql = """
        SELECT episode_date, topic_category, headline, summary, key_entities, is_continuation
        FROM story_memory
        WHERE episode_date >= %s AND episode_date < %s
        ORDER BY episode_date DESC, id ASC
    """
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (cutoff, ref))
            rows = cur.fetchall()
    for r in rows:
        if isinstance(r.get("episode_date"), date):
            r["episode_date"] = r["episode_date"].isoformat()
    return rows


def get_week_stories(week_end_date: date) -> list[dict]:
    monday = week_end_date - timedelta(days=week_end_date.weekday())
    sql = """
        SELECT episode_date, topic_category, headline, summary, key_entities, is_continuation
        FROM story_memory
        WHERE episode_date >= %s AND episode_date < %s
        ORDER BY episode_date ASC, id ASC
    """
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (monday, week_end_date))
            rows = cur.fetchall()
    for r in rows:
        if isinstance(r.get("episode_date"), date):
            r["episode_date"] = r["episode_date"].isoformat()
    return rows


def get_story_count(days: int = 14) -> int:
    cutoff = date.today() - timedelta(days=days)
    sql = "SELECT COUNT(*) FROM story_memory WHERE episode_date >= %s"
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (cutoff,))
            return cur.fetchone()[0]


def get_stories_for_date(episode_date: date) -> list[dict]:
    sql = """
        SELECT episode_date, topic_category, headline, summary, key_entities, is_continuation
        FROM story_memory
        WHERE episode_date = %s
        ORDER BY id ASC
    """
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (episode_date,))
            rows = cur.fetchall()
    for r in rows:
        if isinstance(r.get("episode_date"), date):
            r["episode_date"] = r["episode_date"].isoformat()
    return rows


def has_stories_for_date(episode_date: date) -> bool:
    sql = "SELECT EXISTS(SELECT 1 FROM story_memory WHERE episode_date = %s)"
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (episode_date,))
            return cur.fetchone()[0]


def prune_old_stories(keep_days: int = 90) -> int:
    cutoff = date.today() - timedelta(days=keep_days)
    sql = """
        UPDATE story_memory
        SET summary = '',
            key_entities = '{}'
        WHERE episode_date < %s AND summary != ''
    """
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (cutoff,))
            pruned = cur.rowcount
        conn.commit()
    if pruned:
        log.info("Pruned detailed summaries from %d old story memories (older than %d days)", pruned, keep_days)
    return pruned


def format_recent_for_prompt(stories: list[dict]) -> str:
    if not stories:
        return ""

    by_date: dict[str, list[dict]] = {}
    for s in stories:
        d = s["episode_date"] if isinstance(s["episode_date"], str) else s["episode_date"].isoformat()
        by_date.setdefault(d, []).append(s)

    headline_norm: dict[str, int] = {}
    for s in stories:
        words = s.get("headline", "").lower().split()[:5]
        norm_key = " ".join(words)
        headline_norm[norm_key] = headline_norm.get(norm_key, 0) + 1

    repeated_headlines = [h for h, count in headline_norm.items() if count >= 2]

    sorted_dates = sorted(by_date.keys(), reverse=True)
    yesterday_headlines: list[str] = []
    if sorted_dates:
        for s in by_date[sorted_dates[0]]:
            yesterday_headlines.append(s.get("headline", "?"))

    lines = ["\n\n=== TOPIC ROTATION RULES (MANDATORY) ==="]
    lines.append("The following topics were covered in recent episodes.")
    lines.append("")
    lines.append("HARD RULES:")
    lines.append("1. DO NOT build today's main narrative around any topic from the MOST RECENT")
    lines.append("   episode listed below. Find a completely different angle or topic.")
    lines.append("2. If a specific headline appears multiple times below, that topic is OVERUSED.")
    lines.append("   Skip it unless a genuinely unprecedented event occurred (e.g., war declared,")
    lines.append("   company collapsed, major policy reversal). Routine updates do NOT qualify.")
    lines.append("3. Prioritize stories that have NEVER appeared below.")
    lines.append("4. If you must reference a continuing story, spend at most 2 sentences on it")
    lines.append("   and use it only as context for a DIFFERENT main narrative.")
    lines.append("")

    if yesterday_headlines:
        lines.append("⚠ YESTERDAY'S STORIES (do NOT lead with these):")
        for h in yesterday_headlines:
            lines.append(f"  - {h}")
        lines.append("")

    if repeated_headlines:
        lines.append("⚠ REPEATED TOPICS (skip these — already covered multiple times):")
        for h in repeated_headlines:
            lines.append(f"  - {h}")
        lines.append("")

    lines.append("Previously covered stories:")
    for ep_date in sorted_dates:
        lines.append(f"--- {ep_date} ---")
        for s in by_date[ep_date]:
            cont = " [FOLLOW-UP]" if s.get("is_continuation") else ""
            lines.append(f"• [{s.get('topic_category', '?')}]{cont} {s.get('headline', '?')}")
            if s.get("summary"):
                lines.append(f"  {s['summary']}")
        lines.append("")

    return "\n".join(lines)


def format_week_for_recap(stories: list[dict]) -> str:
    if not stories:
        return ""

    by_date: dict[str, list[dict]] = {}
    for s in stories:
        d = s["episode_date"] if isinstance(s["episode_date"], str) else s["episode_date"].isoformat()
        by_date.setdefault(d, []).append(s)

    lines = ["\n\n=== THIS WEEK'S STORIES (for Sunday recap) ==="]
    lines.append("Below are all stories covered Monday through Saturday this week.")
    lines.append("Your job: reflect on the week, connect arcs, identify emerging patterns,")
    lines.append("and weave a cohesive weekly narrative. Reference specific episodes and")
    lines.append("how stories evolved over the week.\n")

    for ep_date in sorted(by_date.keys()):
        lines.append(f"--- {ep_date} ---")
        for s in by_date[ep_date]:
            cont = " [FOLLOW-UP]" if s.get("is_continuation") else ""
            lines.append(f"• [{s.get('topic_category', '?')}]{cont} {s.get('headline', '?')}")
            if s.get("summary"):
                lines.append(f"  {s['summary']}")
        lines.append("")

    return "\n".join(lines)


def extract_story_summaries(script: list[dict], episode_date: date) -> list[dict]:
    dialogue = "\n".join(
        f"{t['speaker']}: {t['text']}" for t in script if t.get("speaker") != "SFX"
    )

    if len(dialogue) < 100:
        log.warning("Script too short for story extraction")
        return []

    recent = get_recent_stories(days=7, before_date=episode_date)
    recent_headlines = [s.get("headline", "").lower() for s in recent]
    recent_context = ""
    if recent_headlines:
        recent_context = (
            "\n\nFor reference, these headlines were covered recently — if any of today's "
            "stories are follow-ups to these, set is_continuation to true:\n"
            + "\n".join(f"- {h}" for h in recent_headlines if h)
        )

    extraction_prompt = f"""Analyze this podcast transcript and extract each distinct news story or topic discussed.

For each story, return a JSON object with:
- "topic_category": one of "toronto_canada", "global_macro", "ai_tech", "behavioural_spirituality"
- "headline": a concise headline (max 15 words)
- "summary": 2 sentences capturing the specific angle/insight discussed (not just what happened, but the hosts' take)
- "key_entities": list of key people, companies, or concepts mentioned
- "is_continuation": boolean — true if this is a follow-up to a previously covered story
{recent_context}

Return ONLY a JSON array. No markdown, no explanation.

TRANSCRIPT:
{dialogue[:8000]}"""

    try:
        from script_writer import _call_model
        import settings as podcast_settings
        settings = podcast_settings.load()
        model_key = settings.get("script_model", "claude-opus")

        raw, _ = _call_model(
            model_key,
            "You extract structured story data from podcast transcripts. Return ONLY valid JSON.",
            extraction_prompt,
        )
        raw = raw.strip()

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        stories = json.loads(raw)
        if not isinstance(stories, list):
            log.warning("Story extraction returned non-list: %s", type(stories))
            return []

        valid = []
        for s in stories:
            if isinstance(s, dict) and s.get("headline"):
                valid.append({
                    "topic_category": s.get("topic_category", "general"),
                    "headline": s["headline"][:200],
                    "summary": (s.get("summary") or "")[:500],
                    "key_entities": s.get("key_entities", [])[:10],
                    "is_continuation": bool(s.get("is_continuation", False)),
                })
        log.info("Extracted %d story summaries from script", len(valid))
        return valid

    except Exception as exc:
        log.error("Story extraction failed: %s", exc)
        return []
