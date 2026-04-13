# MASTER ARCHITECTURE — Mind Stream Podcast SaaS
## Human-Centered Design Redesign

**Author:** Claude (Anthropic) — architectural synthesis
**Date:** 2026-03-29
**Branch:** claude/human-centered-architecture-plan-eyZR0
**Methodology:** IDEO Human-Centered Design (Discover → Define → Develop → Deliver)
**Source Material:** GAP-AUDIT.md + PRD.md critique

---

## Table of Contents

1. [The Problem We Actually Solve](#1-the-problem-we-actually-solve)
2. [Human-Centered Audit — What the GAP Report Really Tells Us](#2-human-centered-audit)
3. [Revised Product Strategy](#3-revised-product-strategy)
4. [Product Deep Dives](#4-product-deep-dives)
5. [Phased Technical Implementation](#5-phased-technical-implementation)
6. [Key Design Principles](#6-key-design-principles)
7. [Architecture Decisions — Kill / Keep / Simplify](#7-architecture-decisions)
8. [Data Model & Schema](#8-data-model--schema)
9. [API Architecture](#9-api-architecture)
10. [Infrastructure](#10-infrastructure)
11. [Pricing Redesign](#11-pricing-redesign)
12. [Success Metrics](#12-success-metrics)

---

## 1. The Problem We Actually Solve

### The IDEO Insight: Start With the Human, Not the Technology

The original PRD committed the classic product sin: **it started with the solution** (AI podcast generation backend) and worked backward to find personas. IDEO calls this "technology push" — the opposite of human-centered design.

The result was five products solving five different problems, none of them with enough depth to create genuine user loyalty.

**The real pain point, surfaced by the GAP audit:**

> Podcast discoverability is broken. 80% of shows never reach episode 10. The people who could benefit most from podcasting — founders, thought leaders, researchers — don't publish consistently because the friction is too high.

This is a **creator confidence problem**, not a technology problem.

The technology we have (AI audio synthesis, script generation) is the enabler. The real product is **removing the psychological and logistical barriers** between "I have something to say" and "people heard me say it."

### Reframed Mission Statement

**Before:** "AI podcast generation from content sources with two-host audio synthesis."

**After:** "We turn your expertise into a consistent publishing habit. Record once. Ship weekly. Sound like a pro from day one."

This matters because:
- It shifts pricing power from per-feature to outcomes
- It creates emotional hooks (habits, authority, consistency)
- It differentiates from pure API tools

---

## 2. Human-Centered Audit

### What the GAP Report Really Tells Us

The gap audit lists missing features. But reading between the lines, the human-centered signal is different:

#### ScriptFlow
**Feature gap:** "Basic textarea, not WYSIWYG"
**Human gap:** Writers need to *feel* like their creative process is respected. A plain textarea signals "we don't take your craft seriously."
**IDEO insight:** The empty state is the most important screen. An empty textarea is a white wall — paralysis. A WYSIWYG with 5 pre-loaded topic suggestions creates forward momentum.

#### VoiceMemo (currently unbuilt)
**Feature gap:** Entire product missing
**Human gap:** Founders and thought leaders have ideas *constantly* — in the shower, between meetings, on a walk. The "record to published" gap (usually 4–6 hours) means most ideas die.
**IDEO insight:** This is the highest-value unbuilt product. The human pain is acute and the solution is clear: voice memo → polished episode in under 10 minutes.

#### CastAPI
**Feature gap:** No actual MCP server
**Human gap:** Developers evaluate APIs in the first 90 seconds. If they can't run a curl command and see a result, they leave.
**IDEO insight:** The current landing page shows a MCP config but has nothing to connect to. This destroys trust. For developers, a working demo is more credible than 1000 words of documentation.

#### BrainCast
**Feature gap:** "Spaced repetition" feature is irrelevant
**Human gap:** The real pivot is B2B. Remote teams are drowning in async updates — Slack messages, Loom videos, Notion docs. A "weekly team podcast" that auto-summarizes the week's work is a genuine pain killer.
**IDEO insight:** The competitor here is NotebookLM (individual use) but nobody is serving the *team* use case well. Internal team podcasts are an untapped enterprise wedge.

#### PodcastForge
**Human gap:** Enterprise sales cycles are 6–18 months. With no traction, no case studies, and no dedicated sales team, this product is a distraction that burns runway.
**IDEO insight:** Defer entirely until $10k MRR on other products creates the credibility and inbound pipeline needed to close enterprise deals.

---

## 3. Revised Product Strategy

### Priority Matrix (Human-Centered)

| Rank | Product | Status | Why Now | Human Pain Score (1–10) |
|------|---------|--------|---------|------------------------|
| 1 | **Memo.fm** (VoiceMemo rename) | Unbuilt | Highest pain, no competitor in niche | 9/10 |
| 2 | **CastAPI** | MVP exists, needs MCP | Developer trust is broken, fixable fast | 8/10 |
| 3 | **ScriptFlow** | MVP exists, needs polish | Empty state kills conversion | 7/10 |
| 4 | **Grow** (new product) | Unbuilt | #1 user request: discoverability | 9/10 |
| 5 | **BrainCast for Teams** | Pivot from individual | B2B wedge, clear differentiation from NotebookLM | 7/10 |
| ∞ | **PodcastForge** | Deferred | Enterprise needs traction first | N/A |

### The "Grow" Insight

Every creator who publishes an episode immediately asks: "How do I get people to hear it?"

None of the existing five products answer this. **Grow** is a discoverability layer that generates, from a finished episode:
- 5 SEO-optimized title variants (A/B testable)
- Show notes with timestamps and key quotes
- 3 tweet threads
- 1 LinkedIn post
- 3 short audiogram clips (15s, 30s, 60s)
- Chapter markers for Apple Podcasts

This is a **multiplier** on all other products, not a standalone product. Every user who publishes an episode via any of our tools gets Grow automatically.

### Strategic Architecture Principle

> Build one incredible thing, then make it work for five personas — not five mediocre things.

The shared backend (audio synthesis, transcript generation) is the foundation. Each product is a **different interface to the same capability**, optimized for a different workflow and emotional context.

---

## 4. Product Deep Dives

---

### 4.1 Memo.fm (Priority 1)

**Tagline:** "You talk. We publish."

**The Human Story:**
Sarah is a 3x founder. She has insights every day. She's been "starting a podcast" for 18 months. Every attempt dies at the script-writing stage. She doesn't want to write — she wants to *speak*. But raw voice memos sound unprofessional.

**Core User Flow:**
```
Open app → Tap record → Talk for 2–8 minutes →
Auto-transcription → AI restructures into clean episode →
Review + approve (< 5 min) → Private RSS feed generated →
Listener notification sent
```

**The "First Listen" Moment:**
Immediately after generation, the episode auto-plays the first 30 seconds with a waveform animation. This is the emotional peak — Sarah hears her own voice, polished, sounding like a pro. This is the dopamine hit that creates the publishing habit.

**Key Constraints:**
- Record button must be reachable in ≤ 2 taps from any screen
- Total time from "stop recording" to "publishable episode" ≤ 8 minutes
- Works on mobile web (no app install required for MVP)
- Private by default (RSS feed only shared if user chooses)

**Technical Requirements:**
- WebRTC audio capture (browser-native, no install)
- Audio quality normalization (pydub: noise reduction, volume leveling, silence trimming)
- Transcription: AssemblyAI for accuracy, Whisper as fallback (cost control)
- AI restructuring: Claude Haiku prompt chain → intro hook → 3 main points → outro CTA
- Private RSS feed with unique token per subscriber
- Push notification via web push API

**Anti-patterns to avoid:**
- Do NOT ask for a title before recording (friction)
- Do NOT show a waveform during recording (distraction)
- Do NOT allow editing the transcript (kills the "just talk" promise)
- Do NOT auto-publish (user must consciously approve)

---

### 4.2 CastAPI (Priority 2)

**Tagline:** "The Media Generation Protocol."

**The Human Story:**
Arjun is a senior engineer at a B2B AI startup. He wants to add "generate a podcast episode" to his company's content workflow. He opens the CastAPI landing page, sees a MCP config, tries to connect Claude to it, and gets a connection error. He closes the tab and never comes back.

**The Fix — Hero Above the Fold:**
```bash
# This must work before anything else matters
curl -X POST https://api.castapi.io/v1/generate \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"source": "https://techcrunch.com/your-article", "hosts": 2, "duration": 5}'

# Response in < 30 seconds:
{"episode_url": "https://cdn.castapi.io/ep_xyz.mp3", "transcript": "..."}
```

**Real MCP Server Architecture:**
```
┌─────────────────────────────────────┐
│           MCP Client (Claude)        │
│  "Generate episode from this URL"    │
└──────────────────┬──────────────────┘
                   │ JSON-RPC over HTTP
┌──────────────────▼──────────────────┐
│         CastAPI MCP Server           │
│  Tools: generate_episode,            │
│         get_episode_status,          │
│         list_voices,                 │
│         create_series               │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│       Podcast Generation Backend     │
│  (existing Python pipeline)          │
└─────────────────────────────────────┘
```

**MCP Tool Definitions:**

```json
{
  "tools": [
    {
      "name": "generate_episode",
      "description": "Generate a podcast episode from a content source",
      "inputSchema": {
        "type": "object",
        "properties": {
          "source": {"type": "string", "description": "URL, text, or file path"},
          "hosts": {"type": "integer", "enum": [1, 2], "default": 2},
          "duration_minutes": {"type": "integer", "minimum": 2, "maximum": 30},
          "voice_preset": {"type": "string", "description": "Voice pair ID"}
        },
        "required": ["source"]
      }
    },
    {
      "name": "get_episode_status",
      "description": "Poll generation status for async jobs",
      "inputSchema": {
        "type": "object",
        "properties": {
          "job_id": {"type": "string"}
        },
        "required": ["job_id"]
      }
    }
  ]
}
```

**Webhook Architecture:**
- All generation jobs are async (30s–3min)
- `POST /v1/webhooks` to register callback URL
- Webhook payload on completion: `{job_id, episode_url, transcript_url, duration_seconds, cost_credits}`
- Retry logic: exponential backoff, 3 attempts, dead letter queue after failure

**Developer Dashboard Requirements:**
- API key generation + rotation
- Usage graph (episodes generated / credits consumed)
- Webhook log with payload inspection
- Rate limit status
- "Try it now" sandbox with pre-filled examples

---

### 4.3 ScriptFlow Polish (Priority 3)

**Tagline:** "Sound like you rehearsed."

**The Empty State Problem — IDEO Design Principle:**

> "The most important screen is the first one. If a user opens your product and sees a blank cursor, you've already lost."

**Current state:** Plain `<textarea>` with placeholder "Write your script here..."
**Proposed state:** WYSIWYG editor that opens with 5 auto-generated topic suggestions based on the user's niche (set during onboarding).

**WYSIWYG Editor — Tiptap Implementation:**

```typescript
// Editor extensions needed
import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import SpeakerLabel from './extensions/SpeakerLabel'; // custom
import AudioCue from './extensions/AudioCue'; // custom

const editor = new Editor({
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: ({ node }) => {
        if (node.type.name === 'heading') return 'Episode title...';
        return 'Start writing, or pick a topic above ↑';
      }
    }),
    SpeakerLabel, // [HOST 1] / [HOST 2] inline labels
    AudioCue,    // [MUSIC FADE IN] / [PAUSE] markers
  ]
});
```

**Backend Script Storage:**
- Replace `localStorage` with Postgres `scripts` table
- Auto-save every 30 seconds (debounced)
- Versioning: keep last 10 revisions per script
- Schema: `id, user_id, title, content_json, voice_preset, podcast_id, created_at, updated_at`

**Voice Preview Feature:**
- Generate first 30 seconds of audio using current script content
- Uses same backend pipeline but truncated
- Preview plays inline with waveform (Wavesurfer.js)
- Costs 0.1 credits (not free — prevents abuse)

---

### 4.4 Grow Layer (Priority 4 — New)

**Tagline:** "Published isn't enough. Get heard."

**Integration Architecture:**

Grow is not a separate product — it's a **post-publish step** injected into every product's publishing flow.

```
[User clicks Publish] → Episode generated → Grow layer activates →
  ┌─ SEO titles (5 variants, Claude Haiku)
  ├─ Show notes (timestamped, Claude Haiku)
  ├─ Twitter/X thread (3 tweets)
  ├─ LinkedIn post
  └─ Audiogram clips (3 durations via ffmpeg)
→ User reviews Grow output → One-click publish to social
```

**LLM Cost Strategy:**
- Show notes + titles: Claude Haiku (`claude-haiku-4-5`) — fast, cheap, good enough
- Full script generation: Claude Opus (`claude-opus-4-6`) — quality matters here
- Ratio: ~10 Haiku calls per 1 Opus call keeps costs under control

**Audiogram Generation:**
```python
# ffmpeg command for audiogram clip extraction
import subprocess

def generate_audiogram_clip(audio_path: str, start_sec: int, duration: int, output_path: str):
    subprocess.run([
        'ffmpeg', '-i', audio_path,
        '-ss', str(start_sec),
        '-t', str(duration),
        '-filter_complex',
        '[0:a]showwaves=s=640x120:mode=cline:colors=white[v]',
        '-map', '[v]', '-map', '0:a',
        '-y', output_path
    ], check=True)
```

---

### 4.5 BrainCast for Teams (Priority 5)

**Pivot from:** Individual learner turning research into personal audio
**Pivot to:** Engineering/product teams replacing async Slack updates with weekly internal podcasts

**The Human Story:**
A 12-person remote startup. Every Friday, someone spends 3 hours writing the company update. Nobody reads it. With BrainCast for Teams, they upload the week's Notion docs, GitHub commit summaries, and Slack highlights — and get a 10-minute "Weekly Dispatch" podcast that everyone actually listens to on their commute.

**Core Differentiator from NotebookLM:**
NotebookLM is for individuals studying documents. BrainCast for Teams is for organizations communicating internally. The output is private, subscription-based, and recurring — not one-off.

**B2B Architecture Requirements:**
- Organization accounts (not just user accounts)
- Document upload: Notion API integration, Google Drive OAuth, file upload (PDF, DOCX)
- Private RSS feed per organization (authenticated, token-gated)
- Episode scheduling: cron-based weekly auto-generation
- Listener analytics per team member
- Admin dashboard for content managers

---

## 5. Phased Technical Implementation

### Phase 0 — Foundation (Week 1–2) — BLOCKER FOR EVERYTHING ELSE

> Nothing ships on a broken foundation. Fix production infrastructure before writing user features.

**0.1 Database Migration: SQLite → PostgreSQL**

```python
# Current: SQLite (saas_podcast.db) — NOT safe for production
# Target: PostgreSQL (Neon serverless or Fly.io Postgres)

# Migration steps:
# 1. Schema export from SQLite
# 2. Type mapping (SQLite TEXT → PG VARCHAR/TEXT, INTEGER → BIGINT)
# 3. Data migration script (one-time, with validation)
# 4. Update DATABASE_URL in environment
# 5. Run Alembic migrations from scratch against fresh PG instance

# New DATABASE_URL format:
DATABASE_URL=postgresql+asyncpg://user:pass@host/mindstream
```

**Alembic Setup:**
```bash
uv add alembic asyncpg
alembic init alembic
# Edit alembic/env.py to use async engine
alembic revision --autogenerate -m "initial_postgres_schema"
alembic upgrade head
```

**0.2 Production CORS Fix:**
```python
# main.py — replace wildcard CORS
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "https://scriptflow.ai",
    "https://memo.fm",
    "https://castapi.io",
    "https://braincast.fm",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**0.3 Background Job Queue — APScheduler:**
```python
# Jobs that cannot run synchronously:
# - Audio generation (30s–3min)
# - Transcription (10–60s)
# - Grow layer content generation (5–15s)
# - Webhook delivery with retries

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = AsyncIOScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=DATABASE_URL)},
    job_defaults={"coalesce": False, "max_instances": 3},
)

# Job example
scheduler.add_job(
    deliver_webhook,
    "date",
    run_date=datetime.utcnow() + timedelta(seconds=5),
    args=[webhook_id],
    misfire_grace_time=300,
)
```

---

### Phase 1 — Memo.fm (Week 3–5)

**1.1 WebRTC Audio Capture:**
```javascript
// frontend/src/components/Recorder.jsx
const startRecording = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      sampleRate: 44100,
    }
  });

  const mediaRecorder = new MediaRecorder(stream, {
    mimeType: 'audio/webm;codecs=opus'
  });

  const chunks = [];
  mediaRecorder.ondataavailable = e => chunks.push(e.data);
  mediaRecorder.onstop = () => uploadAudio(new Blob(chunks, { type: 'audio/webm' }));
  mediaRecorder.start(1000); // collect data every 1s
};
```

**1.2 Audio Processing Pipeline:**
```python
# podcast/audio_processor.py
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import noisereduce as nr
import numpy as np

def process_voice_memo(input_path: str, output_path: str) -> dict:
    audio = AudioSegment.from_file(input_path)

    # Normalize volume
    audio = normalize(audio)

    # Remove silence (trim leading/trailing + long pauses)
    audio = audio.strip_silence(silence_len=1000, silence_thresh=-40, padding=200)

    # Noise reduction
    samples = np.array(audio.get_array_of_samples())
    reduced = nr.reduce_noise(y=samples, sr=audio.frame_rate)
    audio = AudioSegment(
        reduced.tobytes(),
        frame_rate=audio.frame_rate,
        sample_width=audio.sample_width,
        channels=audio.channels,
    )

    # Export as MP3 for web compatibility
    audio.export(output_path, format="mp3", bitrate="128k")

    return {
        "duration_seconds": len(audio) / 1000,
        "output_path": output_path,
    }
```

**1.3 Private RSS Feed Generation:**
```python
# podcast/rss_generator.py
from feedgen.feed import FeedGenerator
import secrets

def create_private_feed(user_id: int, episodes: list[Episode]) -> str:
    """Generate authenticated RSS feed URL with subscriber token."""
    token = secrets.token_urlsafe(32)

    # Store token → user mapping
    db.execute(
        "INSERT INTO rss_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
        (token, user_id, datetime.utcnow())
    )

    fg = FeedGenerator()
    fg.id(f"https://memo.fm/feed/{token}")
    fg.title(f"{user.display_name}'s Memo.fm Feed")
    fg.link(href=f"https://memo.fm/feed/{token}", rel="self")
    fg.author({"name": user.display_name})

    for episode in episodes:
        fe = fg.add_entry()
        fe.id(episode.episode_url)
        fe.title(episode.title)
        fe.description(episode.show_notes)
        fe.enclosure(episode.episode_url, episode.file_size, "audio/mpeg")
        fe.published(episode.published_at)

    return fg.rss_str(pretty=True)
```

---

### Phase 2 — CastAPI MCP Server (Week 6–8)

**2.1 MCP Server Implementation:**
```python
# castapi/mcp_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

mcp_app = FastAPI(title="CastAPI MCP Server")

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int
    method: str
    params: dict[str, Any] = {}

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int
    result: Any = None
    error: dict | None = None

@mcp_app.post("/mcp")
async def handle_mcp(request: MCPRequest) -> MCPResponse:
    match request.method:
        case "tools/list":
            return MCPResponse(id=request.id, result={"tools": TOOL_DEFINITIONS})
        case "tools/call":
            tool_name = request.params.get("name")
            tool_args = request.params.get("arguments", {})
            result = await execute_tool(tool_name, tool_args)
            return MCPResponse(id=request.id, result=result)
        case _:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": "Method not found"}
            )
```

**2.2 Webhook System:**
```python
# castapi/webhooks.py
import httpx
import asyncio

async def deliver_webhook(webhook_id: str, max_retries: int = 3):
    webhook = await db.get_webhook(webhook_id)
    payload = await db.get_webhook_payload(webhook_id)

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.callback_url,
                    json=payload,
                    headers={
                        "X-CastAPI-Signature": sign_payload(payload, webhook.secret),
                        "X-CastAPI-Event": payload["event"],
                    }
                )
                if response.status_code < 300:
                    await db.mark_webhook_delivered(webhook_id)
                    return
        except Exception as e:
            pass

        # Exponential backoff: 5s, 25s, 125s
        if attempt < max_retries - 1:
            await asyncio.sleep(5 ** (attempt + 1))

    await db.mark_webhook_failed(webhook_id)
```

---

### Phase 3 — ScriptFlow Polish (Week 9–10)

**3.1 Backend Script Storage:**
```sql
-- New scripts table (PostgreSQL)
CREATE TABLE scripts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(255),
    content     JSONB NOT NULL DEFAULT '{}',
    voice_preset VARCHAR(50),
    podcast_id  INTEGER REFERENCES podcasts(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE script_versions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    script_id   UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    content     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON scripts
    FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
```

---

### Phase 4 — Grow Layer (Week 11–12)

**4.1 Content Generation Pipeline:**
```python
# grow/generator.py
import anthropic

client = anthropic.Anthropic()

async def generate_show_notes(transcript: str, episode_duration: int) -> dict:
    """Use Claude Haiku for cost-effective show notes generation."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Generate show notes for this podcast transcript.

Transcript:
{transcript[:4000]}  # truncate for cost control

Episode duration: {episode_duration} minutes

Return JSON with:
- title_variants: 5 SEO-optimized title options
- show_notes: 200-word summary with 3 key timestamps
- tweet_thread: 3-tweet thread
- linkedin_post: 150-word post
- chapter_markers: list of {{time_seconds, title}} for key moments"""
        }]
    )

    return json.loads(response.content[0].text)
```

---

### Phase 5 — BrainCast for Teams (Week 13–16)

**5.1 Document Ingestion:**
```python
# braincast/ingest.py
from notion_client import AsyncClient as NotionClient
from googleapiclient.discovery import build

async def ingest_notion_page(page_id: str, notion_token: str) -> str:
    """Extract plain text from a Notion page."""
    client = NotionClient(auth=notion_token)
    page = await client.pages.retrieve(page_id=page_id)
    blocks = await client.blocks.children.list(block_id=page_id)
    return extract_text_from_blocks(blocks.results)

async def ingest_google_doc(doc_id: str, credentials) -> str:
    """Extract plain text from a Google Doc."""
    service = build('docs', 'v1', credentials=credentials)
    doc = service.documents().get(documentId=doc_id).execute()
    return extract_text_from_gdoc(doc)
```

**5.2 Organization Schema:**
```sql
CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    plan        VARCHAR(50) NOT NULL DEFAULT 'starter',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE org_members (
    org_id      UUID NOT NULL REFERENCES organizations(id),
    user_id     INTEGER NOT NULL REFERENCES users(id),
    role        VARCHAR(50) NOT NULL DEFAULT 'member', -- admin, member, listener
    PRIMARY KEY (org_id, user_id)
);

CREATE TABLE org_feeds (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID NOT NULL REFERENCES organizations(id),
    name        VARCHAR(255) NOT NULL,
    rss_token   VARCHAR(64) UNIQUE NOT NULL,
    schedule    VARCHAR(50), -- cron expression, e.g. "0 9 * * 5" for Friday 9am
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 6. Key Design Principles

### 6.1 Memo.fm — Zero Friction

> "Record button < 2 taps from any screen."

- App opens directly to recording screen (no login wall for first session)
- Bottom navigation: Record (center, prominent), Library, Profile
- During recording: only a waveform and a stop button — no settings, no options
- After stop: single "Publish when ready" CTA — no intermediate steps
- "First Listen" moment mandatory: auto-play first 30 seconds with animation

### 6.2 CastAPI — Developer Trust

> "Working curl command hero above the fold, before any explanation."

- API key visible and copyable immediately after sign-up (no email confirmation gate)
- Interactive playground embedded in the landing page (not a separate docs site)
- Every error response includes `suggestion` field with actionable fix
- Status page at `status.castapi.io` — always visible, never hidden

### 6.3 ScriptFlow — Creator Confidence

> "Empty state must have 5 topic suggestions, not a blank cursor."

- Onboarding collects: niche/topic, target audience, publishing frequency
- Dashboard pre-populates with 5 personalized script starters using Claude Haiku
- Script editor shows estimated episode length in real-time as user types
- "Sound check" button available at any time — never make user wait until end

### 6.4 Universal — "First Listen" Moment

Every product that generates audio must implement the "First Listen" moment:

```javascript
// Trigger after any audio generation completes
const triggerFirstListen = (audioUrl: string) => {
  const audio = new Audio(audioUrl);

  // Show waveform animation overlay
  showWaveformOverlay({
    message: "Your episode is ready.",
    subtext: "Hear the first 30 seconds →",
    autoPlay: true,
    duration: 30,
    onDismiss: () => showPublishFlow(),
  });

  audio.play();

  // Auto-stop at 30 seconds
  setTimeout(() => {
    audio.pause();
    showPublishFlow();
  }, 30000);
};
```

### 6.5 Pricing Language

> "Price on outcomes, not features."

**Don't say:** "3 scripts/month"
**Do say:** "3 published episodes/month"

**Don't say:** "5 podcast shows"
**Do say:** "5 active publishing channels"

This language shift:
- Ties the product to user success (publishing = value delivered)
- Creates natural upgrade pressure as users succeed
- Feels like partnership, not metering

---

## 7. Architecture Decisions — Kill / Keep / Simplify

### KILL

| What | Why |
|------|-----|
| SQLite in production | Data loss risk, no concurrent writes, can't scale |
| PodcastForge | Enterprise needs traction; this is premature complexity |
| Custom voice cloning | Requires training data, trust, legal complexity. Use MiniMax TTS API |
| Spaced repetition in BrainCast | Solving a non-existent user problem (app store feature theater) |
| Wildcard CORS (`*`) | Security risk; replace with explicit origin allowlist |
| localStorage for scripts | Silent data loss on browser clear; move to database |

### KEEP

| What | Why |
|------|-----|
| FastAPI backend | Excellent async support, type safety, OpenAPI auto-docs |
| Two-host audio synthesis | Core differentiator; no competitor does this as smoothly |
| Shared backend architecture | One pipeline, five products — the economics make sense |
| Content-from-URL ingestion | Power feature; ScriptFlow + CastAPI users love this |

### SIMPLIFY

| What | From | To |
|------|------|----|
| LLM routing | One model for everything | Claude Opus for scripts, Claude Haiku for metadata |
| Auth | Rolling custom sessions | Standard JWT + refresh tokens |
| File storage | Local filesystem in container | Object storage (R2 or S3) — persists across deploys |
| Episode distribution | Manual RSS URL | Integration with Spotify/Apple Podcasts Submission API |

---

## 8. Data Model & Schema

### Core Tables (PostgreSQL)

```sql
-- Users
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255),
    display_name    VARCHAR(100),
    niche           VARCHAR(100),
    plan            VARCHAR(50) NOT NULL DEFAULT 'free',
    credits         INTEGER NOT NULL DEFAULT 100,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Podcasts (shows)
CREATE TABLE podcasts (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id          UUID REFERENCES organizations(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    product         VARCHAR(50) NOT NULL, -- 'scriptflow', 'memo', 'castapi', 'braincast'
    rss_token       VARCHAR(64) UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
    is_private      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Episodes
CREATE TABLE episodes (
    id              SERIAL PRIMARY KEY,
    podcast_id      INTEGER NOT NULL REFERENCES podcasts(id) ON DELETE CASCADE,
    title           VARCHAR(255),
    transcript      TEXT,
    audio_url       VARCHAR(500),
    duration_seconds INTEGER,
    file_size_bytes BIGINT,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending | processing | ready | failed
    grow_data       JSONB,
    published_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- API Keys (for CastAPI)
CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash        VARCHAR(255) NOT NULL,
    key_prefix      VARCHAR(10) NOT NULL, -- display only, e.g. "ca_sk_..."
    name            VARCHAR(100),
    last_used_at    TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Webhook registrations
CREATE TABLE webhooks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    callback_url    VARCHAR(500) NOT NULL,
    secret          VARCHAR(100) NOT NULL,
    events          TEXT[] NOT NULL DEFAULT '{"episode.ready"}',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Background jobs
CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type            VARCHAR(50) NOT NULL, -- 'generate_episode', 'deliver_webhook', 'grow'
    payload         JSONB NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'queued',
    -- queued | running | done | failed
    attempts        INTEGER NOT NULL DEFAULT 0,
    max_attempts    INTEGER NOT NULL DEFAULT 3,
    scheduled_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 9. API Architecture

### Route Structure

```
/api/v1/
├── auth/
│   ├── POST /register
│   ├── POST /login
│   ├── POST /refresh
│   └── POST /logout
│
├── podcasts/
│   ├── GET  /               (list user's podcasts)
│   ├── POST /               (create podcast)
│   ├── GET  /{id}
│   ├── PUT  /{id}
│   └── DELETE /{id}
│
├── episodes/
│   ├── GET  /               (list episodes for podcast)
│   ├── POST /generate       (trigger async generation)
│   ├── GET  /{id}
│   ├── GET  /{id}/status    (poll job status)
│   └── DELETE /{id}
│
├── memo/
│   ├── POST /upload         (upload voice memo → trigger processing)
│   └── GET  /feed/{token}   (private RSS endpoint)
│
├── scripts/
│   ├── GET  /
│   ├── POST /
│   ├── GET  /{id}
│   ├── PUT  /{id}
│   └── GET  /{id}/versions
│
├── grow/
│   └── POST /generate       (generate marketing content from episode)
│
├── api-keys/                (CastAPI users)
│   ├── GET  /
│   ├── POST /
│   └── DELETE /{id}
│
├── webhooks/
│   ├── GET  /
│   ├── POST /
│   └── DELETE /{id}
│
└── mcp/                     (CastAPI MCP server)
    └── POST /               (JSON-RPC endpoint)
```

### Authentication Middleware

```python
# middleware/auth.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials

    # Check if it's a JWT (web app) or API key (CastAPI)
    if token.startswith("ca_sk_"):
        return await authenticate_api_key(token, db)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = await db.get(User, payload["sub"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## 10. Infrastructure

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      fly.io                              │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  FastAPI App  │  │  Job Worker  │  │  MCP Server   │  │
│  │  (2 replicas) │  │  (1 replica) │  │  (CastAPI)    │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         └─────────────────┼──────────────────┘           │
│                           │                              │
│  ┌────────────────────────▼──────────────────────────┐   │
│  │           PostgreSQL (Neon serverless)             │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │           Cloudflare R2 (audio file storage)      │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    Vercel (Frontend)                     │
│  scriptflow.ai │ memo.fm │ castapi.io │ braincast.fm     │
└─────────────────────────────────────────────────────────┘
```

### Environment Variables

```bash
# Core
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=<256-bit random>
ENVIRONMENT=production

# AI
ANTHROPIC_API_KEY=sk-ant-...

# Audio
ASSEMBLYAI_API_KEY=...
MINIMAX_API_KEY=...

# Storage
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=mindstream-audio

# Integrations (Phase 5)
NOTION_CLIENT_ID=...
NOTION_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

---

## 11. Pricing Redesign

### Principle: Price on Published Episodes, Not Features

| Product | Free | Creator ($19/mo) | Studio ($49/mo) |
|---------|------|-------------------|-----------------|
| **Memo.fm** | 3 published episodes | 20 episodes | Unlimited |
| **ScriptFlow** | 3 published episodes | 20 episodes | Unlimited |
| **CastAPI** | 10 API calls | 500 calls/mo | 5,000 calls/mo |
| **Grow** | Included with any publish | Included | Included |
| **BrainCast Teams** | 1 team feed, 3 members | — | — |
| **BrainCast Teams Pro** | — | — | $99/mo per team |

### Credit System (Internal)

Each action costs credits. Users never see credits — they see episodes. But internally:

| Action | Credit Cost | Notes |
|--------|-------------|-------|
| Generate episode (Opus) | 10 | Full quality |
| Generate show notes (Haiku) | 1 | Cheap, fast |
| Voice preview (30s) | 1 | Prevent abuse |
| Transcription (per minute) | 0.5 | AssemblyAI cost pass-through |
| Audiogram clip | 0.5 | ffmpeg, very cheap |

---

## 12. Success Metrics

### North Star Metric

**Weekly Published Episodes** — the number of audio episodes pushed to an RSS feed or distribution platform in a 7-day window. This is the metric that directly represents value delivered to users (they published something) and correlates with long-term retention.

### Product-Level KPIs

| Product | Activation Metric | Retention Metric | Revenue Metric |
|---------|-------------------|------------------|----------------|
| Memo.fm | First episode published | Episodes/week/user | Upgrade to Creator |
| ScriptFlow | First script created | Scripts that become episodes | Upgrade to Creator |
| CastAPI | First successful API call | API calls/week | Upgrade to API tier |
| Grow | % of episodes that generate show notes | Return rate to Grow | Included in conversion |
| BrainCast Teams | First team episode | Weekly episode cadence | Teams Pro upgrade |

### Design Validation Checkpoints

Before shipping each phase, validate with 5 real users:

1. **Memo.fm:** Can a first-time user go from "record" to "publishable episode" in under 8 minutes without assistance?
2. **CastAPI:** Can a developer make their first successful API call in under 5 minutes after signing up?
3. **ScriptFlow:** Does a new user feel confident (not paralyzed) when the script editor opens for the first time?
4. **Grow:** Do users feel proud enough of the generated social content to actually post it?
5. **BrainCast Teams:** Would a team use this instead of the Friday Slack update?

If the answer to any of these is "no" — **don't ship, redesign**.

---

## Appendix A — Current Codebase State

Based on the GAP audit, here is the true current state of each product:

| Product | Landing | Auth | Core Feature | Backend API | Status |
|---------|---------|------|-------------|-------------|--------|
| ScriptFlow | ✅ | ✅ | ⚠️ textarea | ✅ partial | MVP |
| CastAPI | ✅ | ✅ | ❌ no MCP | ✅ partial | Pre-MVP |
| VoiceMemo / Memo.fm | ✅ landing | ✅ | ❌ no recorder | ❌ | Pre-MVP |
| BrainCast | ✅ | ✅ | ⚠️ basic | ✅ partial | MVP |
| PodcastForge | ✅ | ✅ | ⚠️ landing only | ✅ partial | Deferred |

---

## Appendix B — IDEO Design Principles Applied

This architecture was developed using IDEO's Human-Centered Design process:

1. **Discover** — Analyzed GAP audit as field research data. Identified the real user pain (discoverability + publishing friction) beneath the stated pain (feature gaps).

2. **Define** — Reframed the problem: "Not 'build 5 products' but 'remove the barriers between expertise and audience.'" Defined the North Star metric as Published Episodes.

3. **Develop** — Prioritized by human pain score, not technical complexity. VoiceMemo/Memo.fm rises to Priority 1 because it solves the most acute, unmet human need even though it requires the most new development.

4. **Deliver** — Phased implementation anchored to user validation checkpoints. No phase ships without answering its validation question with real users.

**The IDEO test for every feature decision:** *"Does this remove a barrier between a person and their ability to publish and be heard?"* If not, it doesn't belong in the roadmap.

---

*This document is the authoritative architecture reference for Mind Stream. All product, engineering, and design decisions should be evaluated against the human-centered principles defined here.*

*Last updated: 2026-03-29 | Author: Claude (Anthropic)*
