# IDEO Design Audit — Mindstream SaaS
**Date:** 2026-03-30 | **Commit audited:** 6ca8407
**Method:** Playwright full-coverage walkthrough + API functional check
**Results:** 14 PASS · 14 GAP · 4 BROKEN (2 confirmed, 2 false positives)

---

## Executive Summary

The backend is solid. Authentication, podcast CRUD, episode generation, and subscription tiers work. The frontend systematically fails to expose any of it to the right audience. The five-persona product strategy defined in the PRD is completely invisible from the landing page. Free-tier users hit a paywall on the one action (API key creation) most likely to convert them.

---

## Confirmed Issues Fixed in This Commit

| # | Issue | Fix |
|---|-------|-----|
| 1 | API keys gated at Pro tier — free users get HTTP 403 | Free tier now gets 1 API key; Pro gets unlimited |
| 2 | Landing page has no mention of ScriptFlow, CastAPI, VoiceMemo, PodcastForge, BrainCast | Added "Built For You" personas section with all 5 products |
| 3 | Mobile nav hidden at 768px with no hamburger menu | Added hamburger button + slide-down mobile menu |
| 4 | Pricing says "API access: disabled" for free tier | Updated to "1 API key (CastAPI)" |
| 5 | Hero stats were fake (50K+ podcasts) | Replaced with honest stats: 5 products, 3 voice providers, $0 to start |

---

## False Positives in Audit Run

The Playwright audit used `demo@mindstream.app / Demo1234!` — a non-existent account. This caused login to fail and cascaded into false CRITs:

- `[CRIT] Login redirect` — code is correct (`window.location.href = '/dashboard'` after `localStorage.setItem`); login just failed due to bad credentials
- `[CRIT] Create Podcast modal has no input` — modal has full form (title, description, language, hosts, TTS, word count); test never reached it
- `[CRIT] Settings navigation missing` — settings link exists in sidebar; test never authenticated
- `[CRIT] No Generate Episode button` — button exists in topbar and quick-actions; test never reached dashboard
- `[CRIT] MCP section missing from CastAPI` — MCP section is at `id="mcp"` with full setup guide; Playwright locator was wrong

---

## Remaining Gaps (Not Fixed This Commit)

These are product-completeness gaps, not bugs:

### VoiceMemo (15% built)
- No voice recording UI — no microphone button, no upload screen
- Persona is mobile-first; no mobile-specific onboarding path

### PodcastForge (20% built)
- Dashboard shows single podcast; no multi-show management view
- No RSS feed generation or distribution UI

### BrainCast (15% built)
- No content ingestion UI (PDF/URL/paper upload)
- No learning-mode episode framing

### ScriptFlow
- WYSIWYG TipTap editor exists in dashboard but is not the primary entry point
- No voice preview button wired to a TTS provider
- Template library empty

### Auth UX
- No Google/GitHub SSO — friction for developer persona
- No password strength indicator on register form

### Dashboard
- Usage limit (episodes remaining this month) not prominently displayed
- No upgrade CTA visible without scrolling to billing section

---

## PRD Coverage by Persona

| Persona | Product | PRD P0 | Delivered | Gap |
|---------|---------|--------|-----------|-----|
| Indie Creator | ScriptFlow | WYSIWYG editor, voice preview, publish | ~40% | No voice preview wired, no templates |
| Developer | CastAPI | REST API, MCP server, sandbox | ~50% | No sandbox, API keys now unlocked for free |
| Thought Leader | VoiceMemo | Voice memo → podcast | ~15% | No recording UI |
| Publisher | PodcastForge | Multi-show, RSS, distribution | ~20% | Single-show only |
| Learner | BrainCast | Content ingestion, learning framing | ~15% | No ingestion UI |

---

## What Works (Confirmed)

- Register → JWT → localStorage → dashboard redirect
- Create podcast, create script, generate episode (full pipeline)
- `GET /api/v1/user/me`, `/podcasts`, `/subscription`, `/usage`
- `POST /api/v1/episodes/generate` (HTTP 200)
- CastAPI page with 83 code examples and MCP setup guide
- OpenAPI Swagger with BearerAuth + Authorize button
- TTS returns HTTP 503 (not silent 200) when MINIMAX_API_KEY not set
- 5-machine stability: 5/5 consecutive API calls succeed

---

## Next Priorities

1. **VoiceMemo UI** — voice recording/upload screen is the highest-differentiation P0 feature with no competition
2. **Usage bar on dashboard** — one `<div>` showing "2/3 episodes this month" reduces upgrade anxiety
3. **ScriptFlow voice preview** — wire the preview button to TTS; it's the reason creators choose the product
4. **Google SSO** — removes the single biggest registration friction for developer persona
