# GAP AUDIT — PRD vs Reality

**Date:** March 27, 2026  
**Status:** Honest assessment of what was promised vs what was built

---

## Executive Summary

The 5 apps were built as **landing pages with basic auth** connected to the shared backend. They are NOT the full-featured UX products described in the PRD. This is a critical gap.

**Current State:** Basic MVP with landing page + login/register + simple dashboard links  
**PRD Promise:** Full product experiences designed for specific personas

---

## Gap Analysis by Product

---

### 1. ScriptFlow (Writers, Bloggers)

#### PRD Promised:
| Feature | Status |
|---------|--------|
| Landing page with hero + features + pricing | ✅ Built |
| Script editor with WYSIWYG | ⚠️ Basic textarea, not WYSIWYG |
| Script templates (Interview, Solo, News, Tutorial) | ⚠️ Templates exist but basic |
| Voice preview (generate short audio) | ❌ Not implemented |
| Save/load scripts | ⚠️ localStorage only, not backend |
| Publish flow (creates podcast, generates episode) | ✅ Working |

#### GAPS:
- [ ] **WYSIWYG Editor** — Currently just a plain textarea. Writers need formatting (bold, italic, scene breaks, speaker labels)
- [ ] **Voice Preview** — No way to preview how the script will sound before publishing
- [ ] **Script Versioning** — Can't compare revisions
- [ ] **Script Import** — Can't import from Google Docs, Word, blog posts
- [ ] **Collaboration** — Can't share scripts with editors
- [ ] **Analytics** — No listen stats per script
- [ ] **Custom Voice Cloning** — Can't train voice on own voice

#### What Works:
- Landing page ✅
- Registration/auth ✅
- Publish to podcast ✅

#### What Needs Work:
- Script editor needs formatting toolbar
- Voice preview button
- Backend storage for scripts (not just localStorage)

---

### 2. CastAPI (Developers, AI Agents)

#### PRD Promised:
| Feature | Status |
|---------|--------|
| Landing page with code example above fold | ✅ Built |
| Interactive API sandbox | ⚠️ Basic JSON input/output, no auth |
| Code snippets (Python, curl, JS) | ✅ Built |
| MCP setup instructions + config files | ⚠️ Basic MCP config shown, not downloadable |
| Pricing page | ✅ Built |
| Try-it-now with live API testing | ⚠️ Works but needs API key |

#### GAPS:
- [ ] **MCP Server** — No actual MCP server running. Config is shown but no server to connect to
- [ ] **Webhook System** — No webhook endpoint for async callbacks
- [ ] **Batch Endpoint** — Can't process multiple content sources at once
- [ ] **Streaming Responses** — No Server-Sent Events for real-time generation status
- [ ] **API Key Management UI** — Users can't see/manage their API keys from the app
- [ ] **Usage Dashboard** — No visualization of API usage, rate limits
- [ ] **SDKs** — No official SDKs for Python, JavaScript, etc.

#### What Works:
- Landing page ✅
- Code examples ✅
- Basic sandbox ✅

#### What Needs Work:
- Actual running MCP server
- Webhook support
- API key management dashboard
- Usage analytics

---

### 3. VoiceMemo (Thought Leaders, Founders)

#### PRD Promised:
| Feature | Status |
|---------|--------|
| Landing page with voice recording mockup | ✅ Built |
| "Record" button (simulates recording with progress) | ⚠️ Mock only, not actual recording |
| Auto-enhancement toggle (noise reduction, leveling) | ⚠️ Toggle exists, no actual processing |
| Episode preview before publish | ❌ No preview before publish |
| Scheduled publishing calendar | ❌ Not implemented |
| Private RSS feed preview | ⚠️ Mentioned but no actual RSS feed |

#### GAPS:
- [ ] **Actual Voice Recording** — No WebRTC/microphone access. It's just a mock button
- [ ] **Audio Processing** — No backend for noise reduction, leveling, etc.
- [ ] **Scheduled Publishing** — No cron job or queue for delayed publishing
- [ ] **Private RSS Feed** — No RSS feed generation
- [ ] **Episode Preview** — Can't listen before publishing
- [ ] **Guest Integration** — Can't have co-host episodes
- [ ] **Intro/Outro Templates** — No branded intros/outros
- [ ] **Analytics** — No download stats, listener demographics

#### What Works:
- Landing page ✅
- Mock recording UI ✅

#### What Needs Work:
- Everything. This is a mockup, not a working product.

---

### 4. PodcastForge (Publishers, Agencies)

#### PRD Promised:
| Feature | Status |
|---------|--------|
| Landing page with multi-show dashboard preview | ✅ Built |
| Multi-show dashboard with tabs | ⚠️ Basic tabs, no real multi-show |
| Episode workflow kanban (Draft→Review→Approve→Published) | ⚠️ Mock kanban on landing page only |
| Team member list with roles | ❌ Not implemented |
| Bulk generation queue | ❌ Not implemented |
| Client white-label preview | ❌ Not implemented |

#### GAPS:
- [ ] **Multi-Show CRUD** — Can't actually create/manage multiple shows
- [ ] **Team Roles/Permissions** — No user roles (Admin, Editor, Producer)
- [ ] **Workflow Stages** — Episodes don't have stage status
- [ ] **Bulk Generation** — Can't queue multiple episodes for batch creation
- [ ] **Client Portal** — No white-label interface for clients
- [ ] **Publishing Pipeline** — No draft→review→approve flow
- [ ] **Content Calendar** — No calendar view of scheduled content

#### What Works:
- Landing page ✅
- Kanban mockup ✅

#### What Needs Work:
- Everything related to multi-show management
- Team features
- Workflow automation

---

### 5. BrainCast (Learners, Researchers)

#### PRD Promised:
| Feature | Status |
|---------|--------|
| Landing page with library preview | ✅ Built |
| Personal audio library view | ⚠️ Basic list, not a real library |
| Article/URL import section | ❌ Not implemented |
| "Cast this" button to add content | ❌ Not implemented |
| Spaced repetition review mode | ⚠️ Mentioned but not functional |
| Learning stats (casts, time saved, topics) | ❌ Not implemented |

#### GAPS:
- [ ] **Article Import** — Can't actually fetch and parse articles from URLs
- [ ] **PDF Support** — No PDF upload/processing
- [ ] **Research Paper Format** — No academic citation style
- [ ] **Personal Library Backend** — No database of saved casts
- [ ] **Spaced Repetition Algorithm** — No SM-2 or similar implementation
- [ ] **Learning Analytics** — No tracking of what user learned
- [ ] **Readwise/Pocket Integration** — No sync with read-later apps
- [ ] **Transcript Highlighting** — Can't highlight and sync with audio

#### What Works:
- Landing page ✅
- Library mockup ✅

#### What Needs Work:
- Everything. This is a concept demo, not a working app.

---

## Root Cause Analysis

### Why the Gap Exists

1. **Time pressure** — Built landing pages fast instead of full apps
2. **Misunderstood scope** — Thought "landing page with CTA" was sufficient
3. **Backend dependency** — Apps need backend features that don't exist yet (webhooks, MCP server, scheduled jobs, audio processing)
4. **No persistence layer** — Most apps need database tables that weren't created

### What's Actually Working

1. **Backend API** — Fully functional (auth, podcasts, episodes)
2. **Dashboard** — Works for basic podcast creation
3. **Landing pages** — 5 distinct designs with correct branding

### What Needs to Be Built

| Priority | Item | Affects |
|----------|------|---------|
| 🔴 HIGH | Voice recording (WebRTC) | VoiceMemo |
| 🔴 HIGH | Article URL fetching + parsing | BrainCast |
| 🔴 HIGH | Multi-show database + UI | PodcastForge |
| 🔴 HIGH | MCP Server running | CastAPI |
| 🟡 MED | WYSIWYG script editor | ScriptFlow |
| 🟡 MED | Scheduled publishing queue | VoiceMemo |
| 🟡 MED | Team roles + permissions | PodcastForge |
| 🟡 MED | Private RSS feed generation | VoiceMemo |
| 🟡 MED | API key management UI | CastAPI |
| 🟡 MED | Usage analytics dashboard | CastAPI |
| 🟢 LOW | SDKs (Python, JS) | CastAPI |
| 🟢 LOW | Spaced repetition algorithm | BrainCast |
| 🟢 LOW | Custom voice cloning | All |

---

## Recommendations

### Option A: Focus on 1-2 Apps (Realistic)
Pick the 2 most viable and build them properly:
1. **ScriptFlow** — Most feasible, core editor + backend already exist
2. **CastAPI** — High demand from developers, clear API product

### Option B: Build Missing Backend First
Before more frontend, build:
1. Webhook system
2. MCP Server
3. Scheduled job runner
4. Article URL fetcher
5. Multi-tenancy support

### Option C: Pivot to Content Business
Instead of building tech, use existing tools:
- Use existing podcast tools (Transistor, Buzzsprout)
- Focus on content production
- Build audience first, tech later

---

## Summary

| Product | Current | Gap Size |
|---------|---------|----------|
| ScriptFlow | 40% | Medium — needs WYSIWYG, voice preview |
| CastAPI | 50% | Medium — needs MCP server, webhooks |
| VoiceMemo | 15% | LARGE — needs audio recording + processing |
| PodcastForge | 20% | LARGE — needs multi-show + workflows |
| BrainCast | 15% | LARGE — needs article import + library |

**Bottom line:** We have working landing pages and a working backend. The actual product experiences described in the PRD are 15-50% implemented.

---

_Next step: Decide which path to pursue — Option A (focus 1-2), Option B (backend first), or Option C (pivot to content)_
