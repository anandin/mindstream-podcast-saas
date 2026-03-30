# Mind Stream SaaS — Playwright E2E Test Report

**Date:** 2026-03-29
**App URL:** http://localhost:8765
**Tester:** Claude (automated)

---

## Summary

| Test | Result | HTTP Status |
|------|--------|-------------|
| GET / — Landing page renders | PASS | 200 |
| GET /login — Login form renders | PASS | 200 |
| POST /api/v1/auth/register — Register new user | PASS | 201 |
| POST /api/v1/auth/login — Login returns token | PASS | 200 |
| GET /dashboard — Dashboard renders with token | PASS | 200 |
| POST /api/v1/podcasts — Create podcast | PASS | 201 |
| GET /api/v1/podcasts — List podcasts | PASS | 200 |
| POST /api/v1/scripts — Create script | PASS | 201 |
| GET /api/v1/scripts — List scripts | PASS | 200 |
| POST /api/v1/memo/upload — Memo upload stub | **FAIL** | 404 (route does not exist) |
| GET /docs — Swagger UI | PASS | 200 |
| POST /api/v1/episodes/generate — Generate episode | **FAIL (BUG)** | 500 |
| GET /api/v1/podcasts/{id} — 404 for missing resource | **FAIL (BUG)** | 404 but HTML not JSON |

**Bugs found: 3**

---

## Bug 1 — CRITICAL: `POST /api/v1/episodes/generate` always returns 500

**File:** `/c/Projects/mindstream-podcast-saas/saas/api/main.py`, lines 851–870

**Symptom:** Any authenticated POST to `/api/v1/episodes/generate` returns `500 - Server Error` (HTML).

**Root cause:** The `generate_episode` function body is empty — it contains only `import os` and then implicitly returns `None`. The actual implementation code (lines 871–950+) is unreachable dead code located **after** a `return` statement inside the `get_episode` function that immediately follows. The code was cut-and-pasted incorrectly: the implementation was placed after `return EpisodeResponse.model_validate(episode)` on line 870, making it part of `get_episode`'s unreachable block.

```python
# Line 851 — generate_episode is effectively empty:
@app.post("/api/v1/episodes/generate", response_model=EpisodeResponse)
def generate_episode(request, user, db):
    """Generate a new episode."""
    import os
    # <-- function ends here, returns None -->

# Line 861 — get_episode, whose return is followed by the displaced implementation:
@app.get("/api/v1/episodes/{episode_id}", response_model=EpisodeResponse)
def get_episode(episode_id, user, db):
    ...
    return EpisodeResponse.model_validate(episode)  # line 870
    # Everything below here (lines 871-950+) is DEAD CODE — never executed
    import re
    import base64
    podcast = db.query(Podcast)...  # never reached
```

FastAPI tries to serialize `None` as `EpisodeResponse` and raises a validation error, which triggers the global 500 handler.

**Fix:** Move the episode generation implementation into the `generate_episode` function body, before `get_episode` starts.

---

## Bug 2 — MEDIUM: Global 404/500 error handlers return HTML for API endpoints

**File:** `/c/Projects/mindstream-podcast-saas/saas/app.py`, lines 106–113

**Symptom:** When an API route raises `HTTPException(status_code=404)`, clients receive `text/html; charset=utf-8` with body `<h1>404 - Not Found</h1>` instead of a JSON error object.

**Reproduction:**
```
GET /api/v1/podcasts/9999
Authorization: Bearer <valid_token>

Response: 404 text/html  "<h1>404 - Not Found</h1>"
Expected: 404 application/json  {"detail": "Podcast not found"}
```

**Root cause:** The app-level `exception_handler(404)` in `app.py` overrides FastAPI's default `HTTPException` handler (which returns JSON). Because `app.py` registers the handler on the outer `app`, it intercepts all 404s — including those raised by API routes via `HTTPException`.

```python
@app.exception_handler(404)
async def not_found(request, exc):
    return HTMLResponse("<h1>404 - Not Found</h1>", status_code=404)  # breaks API clients
```

**Fix:** Check `request.url.path` or `Accept` header to decide whether to return HTML or JSON, or register a separate handler for `HTTPException` that returns JSON for `/api/` paths:

```python
from fastapi.exceptions import HTTPException as FastAPIHTTPException

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    return HTMLResponse(f"<h1>{exc.status_code} - Error</h1>", status_code=exc.status_code)
```

The same issue applies to the 500 handler — but in practice it is only triggered for non-API paths since FastAPI handles its own 500s independently.

---

## Bug 3 — LOW: `POST /api/v1/memo/upload` route does not exist (404)

**Symptom:** `POST /api/v1/memo/upload` returns `404 - Not Found`. The route is not registered anywhere in the application. It does not appear in the Swagger UI at `/docs` either.

**Details:** A search of `saas/api/main.py` and `saas/app.py` confirms there is no `/memo/upload` endpoint. The PRD or README may reference this feature, but it has not been implemented.

**Expected behavior per task spec:** Should return 400 (invalid file) or 200 (accepted). Currently returns 404.

---

## Additional Observations

### Dashboard: 403 console error on every page load (free tier users)

**File:** `/c/Projects/mindstream-podcast-saas/saas/dashboard/templates.py`, `loadApiKeys()` function (~line 516)

The dashboard JavaScript calls `GET /api/v1/api-keys` on every load. Free-tier users always receive a 403 response (`"Requires pro subscription or higher"`), which produces a console error on every visit. The `catch` block swallows the error in the UI, but the 403 response is still logged as a network error in the browser console.

**Fix:** Check `state.user.subscription_tier` before calling `loadApiKeys()` and skip the request for free-tier users.

### Register returns 201 (not 200 as described in task spec)

`POST /api/v1/auth/register` returns HTTP 201 (Created). This is correct REST semantics for resource creation. The task description said "returns 200" which is inaccurate — 201 is the right status code and not a bug.

### Favicon missing

`GET /favicon.ico` returns 404 on all pages. Minor cosmetic issue.

---

## Passing Tests — Detail

| Endpoint | Test | Result |
|----------|------|--------|
| GET / | HTML with nav, features, pricing, hero section | PASS — full landing page renders |
| GET /login | Login form with email + password fields, Login/Register tabs | PASS |
| POST /api/v1/auth/register | `{"email":"test_pw@example.com","password":"TestPass123!","name":"Test User"}` | PASS — 201, returns access_token + refresh_token + user object |
| POST /api/v1/auth/login | Same credentials | PASS — 200, returns tokens |
| POST /api/v1/auth/register (duplicate) | Same email again | PASS — 400 "Email already registered" |
| POST /api/v1/auth/login (wrong password) | Wrong password | PASS — 401 "Invalid email or password" |
| GET /api/v1/podcasts (no auth) | No Authorization header | PASS — 401 "Not authenticated" |
| GET /api/v1/podcasts (bad token) | Invalid JWT | PASS — 401 "Invalid or expired token" |
| POST /api/v1/auth/register (short password) | 3-char password | PASS — 422 validation error |
| POST /api/v1/auth/register (invalid email) | "not-an-email" | PASS — 422 validation error |
| GET /dashboard | With token in localStorage | PASS — dashboard renders, shows user email + usage stats |
| POST /api/v1/podcasts | `{"title":"Test Podcast"}` | PASS — 201, id=1 |
| GET /api/v1/podcasts | List | PASS — 200, count=1 |
| POST /api/v1/scripts | `{"title":"Test Script","content":"..."}` | PASS — 201, id=1 |
| GET /api/v1/scripts | List | PASS — 200, count=1 |
| POST /api/v1/podcasts (empty title) | `{"title":""}` | PASS — 422 "Title cannot be empty" |
| GET /healthz | Health check | PASS — 200 `{"status":"ok","service":"mind-the-gap-saas"}` |
| GET /api/v1/user/me | Authenticated | PASS — 200, email correct |
| GET /api/v1/user/subscription | Authenticated | PASS — 200, tier="free" |
| GET /api/v1/user/usage | Authenticated | PASS — 200, all zero stats |
| POST /api/v1/api-keys (free tier) | Attempt to create API key | PASS — 403 "Requires pro subscription or higher" |
| POST /api/v1/scripts/1/generate-preview | With existing script | PASS — 200 `{"audio_url":null,"text":"...","error":"TTS provider not configured"}` |
| GET /docs | Swagger UI | PASS — full Swagger UI loads with all routes listed |
