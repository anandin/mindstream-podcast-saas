#!/usr/bin/env python3
"""
Mind the Gap — Daily Podcast Generator
───────────────────────────────────────
Orchestrates the full pipeline:
  1. Fetch today's news (NewsAPI + RSS) and social reactions (Reddit)
  2. Write a two-host script (Claude Opus 4.6 / adaptive thinking)
  3. Synthesise audio (ElevenLabs GenFM — two voices)
  4. Upload & publish to Transistor.fm

Usage
─────
  # Full run (fetch → write → synthesise → publish)
  python generate_podcast.py

  # Script-only (skips audio + publish — useful for review / dry-run)
  python generate_podcast.py --script-only

  # Save script to a custom path
  python generate_podcast.py --script-only --out /tmp/episode.txt

  # Use a pre-written script (skips news + writing)
  python generate_podcast.py --from-script /tmp/episode.json

  # Skip publishing (generate audio but don't push to Transistor)
  python generate_podcast.py --no-publish

Environment
───────────
  Copy .env.example → .env and fill in your API keys before running.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mind-the-gap")

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def _episode_stem(ep_date: date) -> str:
    return ep_date.strftime("%Y-%m-%d")


def _archive(
    ep_date: date,
    title: str | None = None,
    description: str | None = None,
    transistor_id: str | None = None,
    share_url: str | None = None,
):
    try:
        from episode_store import archive_episode
        row = archive_episode(ep_date, title, description, transistor_id, share_url)
        log.info(
            "=== STEP 5: Episode archived ===\n"
            "  Date:   %s\n"
            "  Words:  %s\n"
            "  Cost:   $%s\n"
            "  Status: %s",
            row.get("episode_date"), row.get("actual_words"),
            row.get("estimated_cost_usd"), row.get("status"),
        )
    except Exception as exc:
        log.error("ARCHIVING FAILED — episode data may be lost: %s", exc, exc_info=True)


def run(args: argparse.Namespace) -> None:
    ep_date: date = date.today()
    stem = _episode_stem(ep_date)

    script_path = OUTPUT_DIR / f"{stem}_script.json"
    transcript_path = OUTPUT_DIR / f"{stem}_transcript.txt"
    audio_path = OUTPUT_DIR / f"{stem}_episode.mp3"

    _story_memory_available = False
    try:
        from story_memory import (
            prune_old_stories, get_recent_stories, get_week_stories,
            format_recent_for_prompt, format_week_for_recap,
            extract_story_summaries, store_stories,
        )
        _story_memory_available = True
    except Exception as exc:
        log.warning("Story memory unavailable (pipeline continues without it): %s", exc)

    if _story_memory_available:
        try:
            log.info("=== STEP 0: Story memory maintenance ===")
            pruned = prune_old_stories(90)
            if pruned:
                log.info("Pruned %d old story memory entries", pruned)
        except Exception as exc:
            log.warning("Story memory pruning failed (non-fatal): %s", exc)

    if args.from_script:
        log.info("Loading script from %s", args.from_script)
        script = json.loads(Path(args.from_script).read_text())
    else:
        from news_fetcher import fetch_daily_news, summarise_for_prompt
        from social_fetcher import fetch_social_reactions, summarise_social_for_prompt
        from script_writer import generate_script, script_to_plain_text

        covered_headlines: list[str] = []
        story_context = ""
        if _story_memory_available:
            try:
                is_sunday = ep_date.weekday() == 6
                if is_sunday:
                    week_stories = get_week_stories(ep_date)
                    if week_stories:
                        story_context = format_week_for_recap(week_stories)
                        log.info("Sunday recap mode: loaded %d stories from this week", len(week_stories))
                    else:
                        log.info("Sunday but no week stories found — running as normal episode")
                else:
                    recent = get_recent_stories(days=6, before_date=ep_date)
                    if recent:
                        story_context = format_recent_for_prompt(recent)
                        covered_headlines = [s.get("headline", "") for s in recent if s.get("headline")]
                        log.info("Story memory: injecting %d recent stories for dedup", len(recent))
            except Exception as exc:
                log.warning("Story memory context fetch failed (non-fatal): %s", exc)

        log.info("=== STEP 1: Fetching news ===")
        news = fetch_daily_news(covered_headlines=covered_headlines or None)
        news_summary = summarise_for_prompt(news)

        log.info("=== STEP 1b: Fetching social reactions ===")
        reactions = fetch_social_reactions()
        social_summary = summarise_social_for_prompt(reactions)

        combined_summary = news_summary + social_summary

        log.info("=== STEP 2: Writing podcast script ===")
        script = generate_script(combined_summary, ep_date, story_context=story_context)

        script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False))
        transcript_path.write_text(script_to_plain_text(script))
        log.info("Script saved → %s", script_path)
        log.info("Transcript saved → %s", transcript_path)

        if _story_memory_available:
            try:
                log.info("=== STEP 2b: Extracting story memories ===")
                summaries = extract_story_summaries(script, ep_date)
                if summaries:
                    store_stories(ep_date, summaries)
                    log.info("Stored %d story memories for %s", len(summaries), ep_date)
                else:
                    log.warning("No story summaries extracted")
            except Exception as exc:
                log.error("Story memory extraction failed (non-fatal): %s", exc)

    if args.script_only:
        out = Path(args.out) if args.out else transcript_path
        from script_writer import script_to_plain_text
        out.write_text(script_to_plain_text(script))
        log.info("Script-only mode — transcript written to %s", out)
        return

    from script_writer import derive_episode_title
    from audio_generator import generate_audio, generate_episode_description

    log.info("=== STEP 3: Synthesising audio ===")
    generate_audio(script, audio_path)

    title = derive_episode_title(script, ep_date)
    description = generate_episode_description(script, title)

    log.info("Episode title: %s", title)

    desc_path = OUTPUT_DIR / f"{stem}_description.txt"
    desc_path.write_text(f"{title}\n\n{description}")
    log.info("Description saved → %s", desc_path)

    if args.no_publish:
        log.info(
            "=== STEP 4 SKIPPED (--no-publish) ===\n"
            "  Audio:  %s\n"
            "  Title:  %s",
            audio_path,
            title,
        )
        _archive(ep_date, title, description)
        return

    from publisher import publish_full_episode

    log.info("=== STEP 4: Publishing to Transistor.fm ===")
    result = publish_full_episode(title, description, audio_path, ep_date)

    log.info(
        "\n"
        "╔══════════════════════════════════════════════════╗\n"
        "║  Episode published!                              ║\n"
        "║  ID:  %-43s║\n"
        "║  URL: %-43s║\n"
        "╚══════════════════════════════════════════════════╝",
        result["episode_id"],
        result["share_url"],
    )

    _archive(ep_date, title, description, result["episode_id"], result["share_url"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mind the Gap — daily podcast generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--script-only",
        action="store_true",
        help="Stop after generating the script (no audio, no publish).",
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="Where to write the transcript when using --script-only.",
    )
    parser.add_argument(
        "--from-script",
        metavar="PATH",
        help="Load a pre-generated JSON script instead of fetching news.",
    )
    parser.add_argument(
        "--no-publish",
        action="store_true",
        help="Generate audio but do NOT publish to Transistor.fm.",
    )
    args = parser.parse_args()

    try:
        run(args)
    except KeyboardInterrupt:
        log.info("Interrupted by user.")
        sys.exit(0)
    except Exception as exc:
        log.error("Pipeline failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
