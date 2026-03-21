# Mind the Gap — Podcast Control Panel

## Overview

"Mind the Gap" is an automated podcast generation system designed to produce Planet Money-style podcasts using AI. It fetches daily news and social media reactions, generates podcast scripts with real quotes, synthesizes dialogue, creates jingles and sound effects, and mixes the final episode. The system includes a human-in-the-loop approval workflow and can automatically publish episodes to Transistor.fm. The project aims to provide insightful audio content for tech executives, AI enthusiasts, and globally curious professionals, focusing on AI & technology, Canadian economics, and global macro trends, blended with behavioral science and spirituality.

## User Preferences

- **Communication style**: The system should be able to provide detailed explanations for complex processes.
- **Workflow**: The user expects an iterative development process, with clear approval steps before major changes or publications.
- **Interaction**: The system should ask for approval before generating audio or publishing episodes.
- **Dashboard Preferences**: The dashboard should have a premium dark theme with a warm, human-centric design, using a deep navy background with purple accents, Inter font, glass-morphism effects for cards, gradient accents, and micro-interactions like hover lifts and smooth transitions. It should be accessible with `prefers-reduced-motion` support and keyboard navigation for its 3-tab interface (Run, Configure, Historical Runs).
- **Security**: The dashboard requires password-protected login using signed session cookies, with all routes protected except `/login` and `/favicon.ico`.
- **Scheduling**: The system should run automatically every day at 6:00 AM EST, triggering a full pipeline run, and skipping if a job is already in progress.

## System Architecture

The system is built with Python 3.12, using FastAPI for the backend and a single-page HTML dashboard for the frontend.

**Core Features & Design:**

- **Content Generation**:
    - **News Fetching** (`news_fetcher.py`): Gathers news from NewsAPI (multiple sub-queries per category for breadth) and 18 RSS feeds across 5 groups (Toronto/Canada, global macro, AI/tech, behavioral science/spirituality, world news).
    - **News Diversity Pipeline** (3-layer dedup in `news_fetcher.py`):
        1. **Article-level dedup**: Title fingerprinting (stop-word removal + Jaccard similarity at 50% threshold) collapses near-identical articles (e.g., 5 "Anthropic sues Pentagon" articles → 1).
        2. **Story memory filtering**: Before articles reach the LLM, they are compared against headlines from the last 6 days of episodes (via `story_memory.get_recent_stories()`). Articles matching previously covered stories are filtered out upstream using 40% similarity threshold. Additionally, **saturated keyword detection** identifies words appearing in 3+ covered headlines (e.g., "oil", "markets") and deprioritizes articles containing 2+ saturated keywords — pushing them to the end of the list so fresh topics get selected first.
        3. **Topic-cluster diversity selection**: Articles are grouped into topic clusters by title similarity, then selected round-robin (one from each cluster per round, max 2 per cluster, 8 per category). Cross-category dedup in `summarise_for_prompt()` prevents the same story appearing in multiple sections.
    - **Social Media Reactions**: Fetches social sentiment via web search (e.g., Reddit, Twitter/X, HackerNews) using `ddgs` package, without requiring credentials.
    - **Script Writing** (`script_writer.py`): Uses LLMs (defaulting to Claude Opus 4.6, with OpenRouter fallbacks like Gemini 3.1 Pro, GPT-5.4, DeepSeek V3.2) to generate Planet Money-style scripts incorporating real quotes from news and social media. System prompt includes TOPIC FRESHNESS rules requiring each episode to lead with a different topic than the previous day. Prompt templates use domain-balanced examples (tech, urban planning, science, culture, spirituality) to avoid biasing the LLM toward any single topic area.
    - **Audio Generation**: Supports two TTS providers selectable via dropdown: **ElevenLabs GenFM** (default, configurable voices) and **OpenAI TTS** (`gpt-4o-mini-tts` model with voice direction instructions for natural podcast delivery — Onyx for Alex, Nova for Maya). The OpenAI path supports editable per-host voice direction prompts that control speaking style, energy, and personality. SFX and jingles always use ElevenLabs regardless of TTS provider.
- **Editorial Controls**:
    - Dashboard sliders for story count (1-8), behavioral economics and spirituality concepts, and topic weight split.
    - Editable prompt sections (Show Identity, Host Alex, Host Maya, Episode Structure) with reset-to-default functionality.
    - Dynamic episode length scaling based on story count (9-17 minutes).
- **Audio Mixing**: Utilizes `pydub` and `ffmpeg` for audio mixing, including configurable pitch-preserving dialogue speed-up (80-130% via ffmpeg `atempo` filter, default 110%), SFX at -15dB, and sequential assembly of jingles, dialogue, and SFX.
- **Human-in-the-Loop Approval**: A dashboard workflow allows users to preview scripts and then approve them for audio generation or direct publication. A yellow "Script ready for review" banner persists on the Run tab when a script is awaiting review.
- **Settings Persistence**: Settings are stored in PostgreSQL (`app_settings` table) as primary store, with `settings.json` as fallback. This ensures voice selections, model choices, and editorial preferences survive re-deployments.
- **Story Memory System** (`story_memory.py`): A PostgreSQL-backed system (`story_memory` table, unique on `episode_date + headline`) tracks covered topics across episodes. Key functions:
    - `extract_story_summaries()`: Uses Claude Sonnet to extract story headlines, summaries, categories, and entities from generated scripts. Upsert-based storage handles reruns idempotently.
    - `format_recent_for_prompt()`: Injects topic rotation rules into the LLM prompt — explicitly lists yesterday's stories as "do NOT lead with these", detects repeated headlines across episodes using normalized first-5-word matching, and enforces hard skip rules.
    - `format_week_for_recap()`: Provides full week context for Sunday recap episodes.
    - `get_recent_stories()`: Rolling 6-day window query. `prune_old_stories()`: 90-day cleanup.
    - All story memory ops are fail-open (wrapped in try/except) — DB issues disable memory but don't block episode generation.
    - Also supplies `covered_headlines` to the news fetcher for upstream article filtering (see News Diversity Pipeline above).
- **Deployment**: Designed for VM deployment with Gunicorn and Uvicorn workers for an always-on setup, necessary for the daily scheduler.

**Episode Structure (Planet Money format):**
1.  Cold Open
2.  Show Intro
3.  Story with Real Quotes
4.  Behavioral Turn
5.  Spiritual/Philosophical Lens
6.  Takeaway

**LLM Configuration**: Supports configurable primary and fallback LLM models, with auto-failover logic and a model comparison feature.

## External Dependencies

-   **LLMs**: Anthropic (for Claude Opus 4.6), OpenRouter (for Gemini 3.1 Pro, GPT-5.4, DeepSeek V3.2).
-   **Audio Synthesis & SFX**: ElevenLabs GenFM, OpenAI TTS (tts-1-hd), ElevenLabs Sound Effects API.
-   **News Aggregation**: NewsAPI (broadened queries with AND/OR for diversity), RSS feeds (Globe and Mail, Financial Post, CBC, Bloomberg, Economist, NYT Economy, TechCrunch, MIT Tech Review, Ars Technica, Wired, IEEE Spectrum, Behavioral Scientist, Psychology Today, NYT World, Guardian World, BBC World).
-   **Social Media Search**: `ddgs` package for DuckDuckGo web searches.
-   **Publishing**: Transistor.fm (optional).
-   **Database**: PostgreSQL for story memory and episode metadata.
-   **Scheduling**: APScheduler for daily episode generation.
-   **Utility**: `pydub` (audio manipulation), `ffmpeg` (audio processing).