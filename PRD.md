# Mind Stream — Multi-Persona Product Strategy

**Status:** DRAFT — For Anand Review  
**Date:** 2026-03-27  
**Author:** Purple (AI Synthesis)

---

## Executive Summary

The same backend (podcast generation pipeline) can be wrapped as **5 different products** for **5 different personas** — each with distinct UX, pricing, and go-to-market. This maximizes addressable market without diluting the core technology.

**Core Backend:** AI podcast generation from news/content sources with two-host audio synthesis.

---

## The 5 Personas

| # | Persona | App Name | Core Job-to-be-Done | Price Sensitivity |
|---|---------|----------|---------------------|-------------------|
| 1 | **The Indie Creator** | **ScriptFlow** | I want to sound professional without writing skills | Medium — will pay $29-79/mo |
| 2 | **The Developer/Agent** | **CastAPI** | I want to integrate podcast generation into my AI workflow via MCP/API | Low — wants volume pricing, API access |
| 3 | **The Thought Leader** | **VoiceMemo** | I want to build authority and reach by publishing daily | High — will pay for quality and convenience |
| 4 | **The Publisher** | **PodcastForge** | I want to manage multiple shows and scale content production | Low — needs team seats, white-label |
| 5 | **The Curious Learner** | **BrainCast** | I want to learn by creating — turns my research into audio | Medium — values learning over publishing |

---

## Detailed Persona Analysis

---

### PERSONA 1: The Indie Creator

**Profile:**
- Solopreneur, blogger, YouTuber, or content creator
- Wants to expand into audio but lacks writing/scripting skills
- Values polish and professionalism
- Needs editorial control before publishing
- Pain: Too time-consuming to write scripts + find voices + edit

**App Name:** **ScriptFlow**  
**Tagline:** *"Turn your ideas into podcast-ready scripts — in minutes."*  
**URL:** scriptflow.ai

**Core Problem:** Wants to publish podcasts but gets stuck at the script writing phase. Either doesn't publish at all, or publishes inconsistent, low-quality content that hurts their brand.

**Jobs-to-be-Done:**
1. Turn a topic/URL/document into a structured podcast script
2. Edit and refine the script before it goes live
3. Preview how the audio will sound with different voice combinations
4. Publish directly to Spotify/Apple from the platform

**Feature Priority:**
| Feature | Priority | Notes |
|---------|----------|-------|
| Script editor with WYSIWYG | P0 | Rich text, two-column view (what's said + audio cues) |
| Script templates | P1 | "Interview", "Solo cast", "News roundup", "Tutorial" |
| Voice preview | P1 | Preview with different voice combos before generating |
| One-click publish to Spotify/Apple | P1 | Distribution built-in |
| Content import (URL, Paste, File) | P0 | Pull from blog posts, articles, docs |
| Script versioning | P2 | Compare revisions |

**UX/UI Direction:**
- Clean, writer-focused interface (like Notion meets Descript)
- Dark mode by default (creatives prefer it)
- Large script editor as hero element
- Minimal dashboard — just "New Script" and "My Scripts"
- Audio waveform visualization for final preview

**Landing Page Vibe:**
- Headline: "Your ideas deserve to be heard."
- Subhead: "ScriptFlow turns any topic into a polished podcast script. No writing skills required."
- Social proof: "Join 2,400+ creators who've published without the sweat."
- CTA: "Start creating for free"

**Pricing:**
| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | 3 scripts/month, Voxtral voice | Standard |
| Pro | $29/mo | Unlimited scripts, 11Labs voice, no watermark, voice preview, publish | Premium |
| Studio | $79/mo | + Custom voices (11Labs), team sharing (3 seats), priority | Premium |

---

### PERSONA 2: The Developer / AI Agent

**Profile:**
- Developer building AI agents or automation workflows
- Wants programmatic access via API or MCP (Model Context Protocol)
- Needs reliable, consistent JSON/API output for downstream processing
- Pain: No good API-first podcast generation tool exists

**App Name:** **CastAPI**  
**Tagline:** *"Podcast generation as a service. For humans and AI agents."*  
**URL:** castapi.dev

**Core Problem:** Existing tools are consumer-grade SaaS (no API). They need programmatic, reliable access for integration into their AI agent loops.

**Jobs-to-be-Done:**
1. Send a URL/content → Get back a complete podcast audio file (or URL to it)
2. Get structured JSON output (script, metadata, audio URL) for agent consumption
3. Webhook/Callback when generation completes
4. Batch generation for content pipelines

**Feature Priority:**
| Feature | Priority | Notes |
|---------|----------|-------|
| REST API with OpenAPI docs | P0 | Full CRUD + webhooks |
| MCP Server | P0 | Direct Claude Desktop/Agent integration |
| Streaming responses | P1 | Real-time generation status |
| Batch endpoint | P1 | Process multiple content sources at once |
| Custom voice cloning | P2 | Enterprise tier |
| Usage analytics + rate limit headers | P0 | Developers need visibility |

**UX/UI Direction:**
- Developer-focused (not consumer)
- Dark terminal aesthetic
- API docs as the main UI — interactive sandbox
- Dashboard shows: API keys, Usage, Rate limits, Webhook logs
- Minimal branding — the API IS the product
- Code snippets front and center (Python, curl, JavaScript examples)

**Landing Page Vibe:**
- Headline: "Podcast generation API for AI agents and developers."
- Subhead: "CastAPI gives your AI agents the ability to generate, synthesize, and publish audio content — in production."
- Code sample above the fold: `curl -X POST https://api.castapi.dev/v1/generate ...`
- Integration logos: Claude, LangChain, AutoGen, n8n
- CTA: "Get your API key →"

**Pricing:**
| Tier | Price | API Calls | Features |
|------|-------|-----------|----------|
| Dev | $0 | 100/mo | Full API, watermarked, Voxtral voice | Standard |
| Growth | $49/mo | 2,000/mo | No watermark, webhooks, priority, Voxtral | High |
| Scale | $199/mo | 10,000/mo | 11Labs voices, SLA, dedicated support | Premium |
| Enterprise | Custom | Unlimited | White-label, MCP, custom SLAs, custom voices | Premium |

---

### PERSONA 3: The Thought Leader

**Profile:**
- Founder, executive, coach, consultant, or public figure
- Wants to build authority and stay top-of-mind through daily audio content
- Has ideas and opinions but no time for production
- Values quality and brand consistency
- Pain: Doesn't have time for traditional content production

**App Name:** **VoiceMemo**  
**Tagline:** *"Your daily thought — broadcast to the world. In your voice."*  
**URL:** voicememo.fm

**Core Problem:** Has valuable insights but the friction of content production means they don't publish consistently. When they do, it's often delayed or diluted.

**Jobs-to-be-Done:**
1. Record a quick voice memo or brain dump
2. Have it transformed into a polished podcast episode automatically
3. Subscribe to auto-publish to their podcast feed
4. Build an audience without managing production

**Feature Priority:**
| Feature | Priority | Notes |
|---------|----------|-------|
| Voice-to-podcast (record → episode) | P0 | Core differentiator |
| Auto-enhancement (noise reduction, leveling) | P0 | Makes their recording sound professional |
| Scheduled publishing | P1 | Set and forget daily/weekly cadence |
| Subscriber feed (private RSS) | P1 | Build audience without Spotify dependency |
| Guest integration | P2 | Co-host episodes |
| "My voice, my style" customization | P1 | Tone, length, intro/outro |

**UX/UI Direction:**
- Voice-first (record button is the hero)
- Clean, minimal, premium feel (like a luxury audio brand)
- Light mode with warm tones (trust, authority, presence)
- App feels like a personal broadcast studio
- "Episodes" tab shows their content calendar

**Landing Page Vibe:**
- Headline: "Your voice. Your ideas. A global audience."
- Subhead: "VoiceMemo transforms your daily thoughts into a polished podcast — automatically. All you do is talk."
- Imagery: Founder recording on phone, with polished episode ready in minutes
- Social proof: "Used by 800+ founders to build their thought leadership"
- CTA: "Start broadcasting — free for 14 days"

**Pricing:**
| Tier | Price | Features |
|------|-------|----------|
| Solo | $19/mo | Unlimited recordings, auto-publish, private feed, 11Labs voice | Premium |
| Pro | $49/mo | + Custom intro/outro, analytics, guest episodes | Premium |
| Brand | $149/mo | + White-label feed, branded app, team (5 seats) | Premium |

---

### PERSONA 4: The Publisher

**Profile:**
- Media company, content agency, or newsletter publisher
- Needs to scale content production across multiple shows/topics
- Wants team collaboration and workflow management
- Pain: Expensive to produce content at scale, coordination overhead

**App Name:** **PodcastForge**  
**Tagline:** *"Scale your podcast empire without scaling your team."*  
**URL:** podcastforge.io

**Core Problem:** Content production doesn't scale linearly — each additional show requires significant overhead. They need to produce more without proportionally increasing costs.

**Jobs-to-be-Done:**
1. Manage multiple podcasts from one dashboard
2. Set content rules/templates per show (different voices, formats, cadences)
3. Collaborate with team (editors, writers, producers)
4. White-label for client work
5. Get analytics across all shows

**Feature Priority:**
| Feature | Priority | Notes |
|---------|----------|-------|
| Multi-show dashboard | P0 | Single pane of glass |
| Show templates (voice, format, intro) | P0 | Reusable show configurations |
| Team roles + permissions | P0 | Editor, Writer, Producer, Admin |
| Workflow stages | P1 | Draft → Review → Approve → Publish |
| Client white-labeling | P1 | Branded portals for clients |
| Bulk generation | P0 | Queue content from RSS/API for batch processing |
| API access for enterprise | P1 | Integrate into existing CMS/publishing pipeline |

**UX/UI Direction:**
- Dashboard-heavy (CMS aesthetic)
- Project management meets podcast production
- Dark sidebar navigation, light content area
- Kanban view for episode workflow stages
- Clear hierarchy: Workspace → Show → Episode → Asset

**Landing Page Vibe:**
- Headline: "From one show to ten — without the chaos."
- Subhead: "PodcastForge gives publishers the infrastructure to scale audio content production without scaling headcount."
- Case study prominent: "How [Agency X] scaled from 3 to 27 shows in 6 months"
- CTA: "Book a demo" (enterprise sales motion)

**Pricing:**
| Tier | Price | Shows | Team Seats | Features |
|------|-------|-------|-----------|----------|
| Starter | $99/mo | 3 | 5 | Full platform, Voxtral voices | High |
| Growth | $299/mo | 10 | 15 | + Workflow, bulk, API, 11Labs voices | Premium |
| Agency | $799/mo | Unlimited | 50 | + White-label, SLA, 11Labs voices | Premium |
| Enterprise | Custom | Unlimited | Unlimited | + Dedicated infra, custom contracts |

---

### PERSONA 5: The Curious Learner

**Profile:**
- Lifelong learner, researcher, student, or knowledge enthusiast
- Creates content to deepen their own understanding
- Values learning process over audience building
- Often creates "audio notes" for later review
- Pain: Passive consumption of content doesn't stick — creating is better learning

**App Name:** **BrainCast**  
**Tagline:** *"Learn by creating. Turn everything you read into podcasts you can listen to."*  
**URL:** braincast.app

**Core Problem:** Reading alone doesn't create deep learning. They consume a lot but forget most. Creating audio summaries forces synthesis and improves retention.

**Jobs-to-be-Done:**
1. Import articles, research papers, or notes
2. Have them synthesized into a conversational audio explainer
3. Review on-the-go (commute, workout, walks)
4. Build a personal audio library of everything they've learned

**Feature Priority:**
| Feature | Priority | Notes |
|---------|----------|-------|
| Article/URL import | P0 | Pocket, Instapaper, Readwise integration |
| Research paper format | P1 | Academic style (cite sources, explain methodology) |
| Personal audio library | P0 | Searchable, taggable audio notes |
| Spaced repetition audio | P2 | "Replay this episode to remember more" |
| Listen later queue | P1 | Add to queue, auto-generate when ready |
| Learning transcripts | P1 | Read along + highlights in transcript |

**UX/UI Direction:**
- Warm, inviting, intellectual aesthetic
- Light mode with warm accent colors (like a good bookshop)
- Library-first (like Apple Books or Notion)
- Simple, focused — just "Add" and "Listen"
- Mobile-first (they listen on the go)

**Landing Page Vibe:**
- Headline: "What you learn, you remember. Turn reading into listening."
- Subhead: "BrainCast transforms articles, papers, and notes into audio explainers — so you can learn everywhere you go."
- Education-forward messaging: "The Feynman Technique meets AI"
- CTA: "Start learning differently — free forever for personal use"

**Pricing:**
| Tier | Price | Features |
|------|-------|----------|
| Personal | $0 | 10 casts/month, personal library, MiniMax voice | Standard |
| Scholar | $14/mo | Unlimited casts, research format, Voxtral voice | High |
| Academic | $39/mo | + Cite sources, PDF import, study modes, 11Labs voice | Premium |

---

## Voice Quality Tiers

We support three voice synthesis providers, tiered by quality and cost. Default selection is based on persona and tier:

| Provider | Quality | Cost | Default For |
|----------|---------|------|-------------|
| **11Labs** | ⭐⭐⭐⭐⭐ Premium | $0.30/1000 chars | Pro/Studio tiers, Thought Leaders, Publishers |
| **Voxtral (Mistral)** | ⭐⭐⭐⭐ High | $0.15/1000 chars | Growth tier, Developers, Indie Creators |
| **MiniMax** | ⭐⭐⭐ Standard | $0.05/1000 chars | Free tier, Learners, budget-conscious |

### Voice Selection Logic

```
IF user.tier == "free" AND persona == "learner":
    DEFAULT voice = "minimax"  # Affordability first
ELIF user.tier in ["pro", "studio"] AND persona in ["thought_leader", "publisher"]:
    DEFAULT voice = "11labs"  # Premium quality for premium users
ELIF user.tier == "growth" AND persona == "developer":
    DEFAULT voice = "voxtral"  # Balance cost/quality for builders
ELSE:
    DEFAULT voice = "voxtral"  # Sensible default
```

### Human-Centered Design Philosophy

**Core Objective:** Solve real human problems and create genuine value. Money is an outcome of value creation — not the driving force.

> *"We are not building a monetization machine. We are building tools that help humans think, learn, create, and share more effectively. Revenue is applause — it tells us we're on the right track."*

### Design Principles

1. **Problem-first, not solution-first** — Every feature starts with: "What human problem does this solve?"
2. **Affordability as a feature** — Free tier users get real value, not a crippled demo
3. **Transparency** — Users know what they're paying for, what data we use, and why
4. **Agency over automation** — Humans control the output, AI assists
5. **Value before monetization** — Every tier must solve the persona's core problem

### Per-Persona Voice + Value Emphasis

| Persona | Core Problem Solved | Voice Default | Value Emphasis |
|---------|---------------------|---------------|----------------|
| Indie Creator | Can't write scripts efficiently | 11Labs (Pro), Voxtral (Free) | "Sound professional without writing skills" |
| Developer | No API-first podcast generation | Voxtral (all tiers) | "Integrate into your workflow, pay for volume" |
| Thought Leader | No time for content production | 11Labs (all tiers) | "Your voice, broadcast to the world" |
| Publisher | Content doesn't scale | 11Labs (Studio), Voxtral (Starter) | "Scale content without scaling team" |
| Learner | Passive learning doesn't stick | MiniMax (Personal), Voxtral (Scholar) | "Learn by creating, not just consuming" |

---

## Technical Architecture

### Shared Backend Components

```
┌─────────────────────────────────────────┐
│           Mind Stream Core               │
├─────────────────────────────────────────┤
│  News/RSS Fetcher           ✓ Built     │
│  Script Writer (LLM)        ✓ Built     │
│  Audio Synth (Multi-Provider) ✓ Built   │
│    ├─ 11Labs               ✓           │
│    ├─ Voxtral (Mistral)    ⚠️ Todo     │
│    └─ MiniMax               ⚠️ Todo    │
│  Podcast Publisher          ✓ Built     │
│  User Auth                  ✓ Built     │
│  API Key Management        ✓ Built      │
│  Usage Tracking            ⚠️ Needs work│
│  Webhook System            ❌ Missing   │
│  MCP Server                ❌ Missing   │
└─────────────────────────────────────────┘
```

### Per-Product Frontend

| Product | Frontend | Backend | Notes |
|---------|----------|---------|-------|
| ScriptFlow | React SPA | Same | Script editor + publish flow |
| CastAPI | Docs + Dev Portal | Same + Extensions | API-first, MCP |
| VoiceMemo | React Native + Web | Same + Voice processing | Voice-first UX |
| PodcastForge | React + Dashboard | Same + Multi-tenancy | CMS-style |
| BrainCast | React + Mobile | Same + Learning features | Library-first |

---

## Implementation Priority

Given Anand's goal of **billion-dollar value creation**, here's recommended build order:

### Phase 1: Core Platform (4-6 weeks)
- [ ] Refactor Mind Stream into proper multi-tenant backend
- [ ] Add webhook system (for CastAPI)
- [ ] Add MCP server (for CastAPI)
- [ ] Build CastAPI developer portal + docs
- [ ] Build ScriptFlow landing + core UX

**Rationale:** CastAPI + ScriptFlow have the clearest product-market fit and lowest customer acquisition cost (developers + indie creators are self-serve).

### Phase 2: Expand (6-10 weeks)
- [ ] Build VoiceMemo (voice-first UX on top of same backend)
- [ ] Build PodcastForge multi-show dashboard
- [ ] Add team features to PodcastForge

**Rationale:** These build on same backend — incremental effort for new personas.

### Phase 3: Learning (10-14 weeks)
- [ ] Build BrainCast with learning features
- [ ] Add research paper format support
- [ ] Build personal library + spaced repetition

**Rationale:** Lower priority but large TAM (education market).

---

## Behavioral Science Applications

### Per-Persona Nudges (Human-Centered)

| Persona | Key Behavior | Nudge Applied |
|---------|--------------|---------------|
| Indie Creator | Come back daily | Streak counter, "Your script is waiting" |
| Developer | Integrate and build | "2 more API calls until your next tier" |
| Thought Leader | Record daily | "You've recorded X days this month" |
| Publisher | Complete workflow stages | Progress bar, "Almost ready to publish" |
| Learner | Consistent review | "Time to review your BrainCast from Tuesday" |

### Hook Model per Product

> **Note:** Nudges are applied ethically — we enhance human goals, not manipulate. Every engagement metric serves the user's stated objective, not vanity metrics.

**ScriptFlow:** Trigger (idea strikes) → Action (write topic) → Reward (hear preview) → Investment (refine script)

**CastAPI:** Trigger (agent needs content) → Action (API call) → Reward (structured JSON) → Investment (integrate deeper)

**VoiceMemo:** Trigger (thought occurs) → Action (record 30s) → Reward (professional episode) → Investment (subscribe to feed)

**PodcastForge:** Trigger (content calendar) → Action (assign to team) → Reward (published episode) → Investment (build library)

**BrainCast:** Trigger (read something interesting) → Action (save to BrainCast) → Reward (listen to summary) → Investment (build personal library)

---

## Competitor Analysis

| Competitor | Strength | Weakness | Our Edge |
|------------|----------|----------|----------|
| **Castmagic** | Well-funded, good product | No API, consumer-only | CastAPI = API-first Castmagic |
| **ElevenLabs** | Voice tech excellent | No content pipeline | We do content + voice |
| **Descript** | Editor is great | Over-focused on editing | We do generation end-to-end |
| **Podcastle** | Good quality, reasonable | No differentiation | Personalization + personas |
| **RSS-to-podcast tools** | Simple, cheap | No AI, purely mechanical | AI synthesis + personalization |
| **NotebookLM** | Great research UX | Audio output is just "nice to have" | Production-ready podcast output |

---

## Summary: One Backend, Five Products

| Product | Name | Tagline | Primary UX | Target |
|---------|------|---------|------------|--------|
| 1 | ScriptFlow | "Turn ideas into scripts" | Editor-centric | Writers |
| 2 | CastAPI | "Podcast API for agents" | API + Docs | Developers |
| 3 | VoiceMemo | "Your voice, your brand" | Voice-first | Thought leaders |
| 4 | PodcastForge | "Scale without scaling" | Multi-show CMS | Publishers |
| 5 | BrainCast | "Learn by creating" | Library | Learners |

---

## Next Steps

1. **Anand reviews** this PRD
2. **Feedback + revisions** — which personas resonate? Which need more/less?
3. **Approve** — lock the PRD in git
4. **Purple goes auto** — builds all 5 products without asking

---

_Built from: Market analysis, competitor research, behavioral science frameworks, design thinking methodology_
_Anand's Rotman + MIT lens applied_
