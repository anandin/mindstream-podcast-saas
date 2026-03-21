#!/usr/bin/env python3
"""
Mind the Gap — Podcast Control Dashboard
─────────────────────────────────────────
Run:  uvicorn server:app --host 0.0.0.0 --port 5000
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator
from zoneinfo import ZoneInfo

import requests as http_requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse, RedirectResponse

log = logging.getLogger("mind-the-gap-server")

# ── Paths & env ────────────────────────────────────────────────────────────────
HERE = Path(__file__).parent
OUTPUT_DIR = HERE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))

from dotenv import load_dotenv
load_dotenv(HERE / ".env")

TRANSISTOR_API_KEY = os.getenv("TRANSISTOR_API_KEY", "")
TRANSISTOR_SHOW_ID = os.getenv("TRANSISTOR_SHOW_ID", "")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

import settings as podcast_settings

_cookie_secret = os.getenv("COOKIE_SECRET") or DASHBOARD_PASSWORD or secrets.token_hex(32)
_signer = URLSafeTimedSerializer(_cookie_secret)
SESSION_COOKIE = "mtg_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7

# ── Job state ──────────────────────────────────────────────────────────────────
_job: dict = {
    "running": False,
    "mode": None,
    "started_at": None,
    "finished_at": None,
    "exit_code": None,
    "log": [],
    "awaiting_approval": False,
    "approval_script_date": None,
}
_sse_queues: list[asyncio.Queue] = []
_active_proc: asyncio.subprocess.Process | None = None

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Mind the Gap Control Panel")

# ── Scheduler ─────────────────────────────────────────────────────────────────
EST = ZoneInfo("America/New_York")
scheduler = AsyncIOScheduler()


async def _scheduled_run():
    if _job["running"]:
        log.info("Scheduled run skipped — a job is already running.")
        return
    log.info("Scheduled daily run triggered at 6:00 AM EST")
    await _run_pipeline("full")


scheduler.add_job(
    _scheduled_run,
    CronTrigger(hour=6, minute=0, timezone=EST),
    id="daily_episode",
    replace_existing=True,
)


@app.on_event("startup")
async def _start_scheduler():
    scheduler.start()
    next_run = scheduler.get_job("daily_episode").next_run_time
    log.info("Scheduler started — next daily run at %s", next_run)


@app.on_event("shutdown")
async def _stop_scheduler():
    scheduler.shutdown(wait=False)


# ── Auth ──────────────────────────────────────────────────────────────────────
PUBLIC_PATHS = {"/login", "/favicon.ico", "/healthz"}


def _is_authenticated(request: Request) -> bool:
    if not DASHBOARD_PASSWORD:
        return True
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return False
    try:
        data = _signer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("auth") == "ok"
    except (BadSignature, SignatureExpired):
        return False


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path in PUBLIC_PATHS or not DASHBOARD_PASSWORD:
        return await call_next(request)
    if _is_authenticated(request):
        return await call_next(request)
    if path.startswith("/api/"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return RedirectResponse("/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    return HTMLResponse(LOGIN_HTML)


@app.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    password = form.get("password", "")
    if hmac.compare_digest(password, DASHBOARD_PASSWORD):
        token = _signer.dumps({"auth": "ok"})
        response = RedirectResponse("/", status_code=302)
        is_https = str(request.url).startswith("https") or request.headers.get("x-forwarded-proto") == "https"
        response.set_cookie(
            SESSION_COOKIE, token,
            max_age=SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=is_https,
        )
        return response
    return HTMLResponse(LOGIN_HTML.replace("<!--ERROR-->", '<div class="error">Incorrect password. Please try again.</div>'))


@app.post("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response

@app.get("/logout")
async def logout_get():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response


# ── Helpers ────────────────────────────────────────────────────────────────────
def _broadcast(line: str) -> None:
    _job["log"].append(line)
    if len(_job["log"]) > 3000:
        _job["log"] = _job["log"][-3000:]
    for q in _sse_queues:
        try:
            q.put_nowait(line)
        except asyncio.QueueFull:
            pass


async def _run_pipeline(mode: str, from_script: str | None = None) -> None:
    _job.update(
        running=True, mode=mode,
        started_at=datetime.now(timezone.utc).isoformat(),
        finished_at=None, exit_code=None, log=[],
        awaiting_approval=False, approval_script_date=None,
    )

    cmd = [sys.executable, str(HERE / "generate_podcast.py")]
    if from_script:
        cmd += ["--from-script", from_script]
        if mode == "no-publish":
            cmd += ["--no-publish"]
    elif mode == "script":
        cmd += ["--script-only"]
    elif mode == "no-publish":
        cmd += ["--no-publish"]

    _broadcast(f"▶ Starting [{mode}] run at {datetime.now():%H:%M:%S}\n")

    import os as _os
    global _active_proc
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(HERE),
        start_new_session=True,
    )
    _active_proc = proc
    async for raw in proc.stdout:
        _broadcast(raw.decode("utf-8", errors="replace"))

    await proc.wait()
    _active_proc = None

    ok = proc.returncode == 0

    if ok and mode == "script":
        from datetime import date as _date
        today_str = _date.today().strftime("%Y-%m-%d")
        _job.update(
            running=False,
            finished_at=datetime.now(timezone.utc).isoformat(),
            exit_code=proc.returncode,
            awaiting_approval=True,
            approval_script_date=today_str,
        )
    else:
        _job.update(
            running=False,
            finished_at=datetime.now(timezone.utc).isoformat(),
            exit_code=proc.returncode,
            awaiting_approval=False,
            approval_script_date=None,
        )

    _broadcast(
        f"{'✓ SUCCESS' if ok else f'✗ FAILED (exit {proc.returncode})'}"
        f" at {datetime.now():%H:%M:%S}\n"
    )
    for q in list(_sse_queues):
        q.put_nowait("__DONE__")


def _scan_local_episodes() -> list[dict]:
    eps = []
    dates_seen: set[str] = set()
    for f in OUTPUT_DIR.iterdir():
        stem = f.stem
        for suffix in ("_description", "_transcript", "_script", "_episode"):
            if stem.endswith(suffix):
                date_str = stem.replace(suffix, "")
                dates_seen.add(date_str)
                break
    for date_str in sorted(dates_seen, reverse=True):
        desc = OUTPUT_DIR / f"{date_str}_description.txt"
        mp3 = OUTPUT_DIR / f"{date_str}_episode.mp3"
        transcript = OUTPUT_DIR / f"{date_str}_transcript.txt"
        script = OUTPUT_DIR / f"{date_str}_script.json"
        title = date_str
        if desc.exists():
            lines = desc.read_text().splitlines()
            title = lines[0] if lines else date_str
        elif transcript.exists():
            first_line = transcript.read_text(errors="replace").split("\n", 1)[0]
            title = f"Script — {date_str}" if not first_line.strip() else first_line[:80]
        generated_at = None
        for candidate in (mp3, transcript, script, desc):
            if candidate.exists():
                generated_at = datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc).isoformat()
                break
        eps.append({
            "date": date_str,
            "title": title,
            "has_audio": mp3.exists(),
            "has_transcript": transcript.exists(),
            "has_script": script.exists(),
            "size_mb": round(mp3.stat().st_size / 1e6, 1) if mp3.exists() else None,
            "generated_at": generated_at,
        })
    return eps


def _fetch_db_episodes() -> list[dict]:
    try:
        from episode_store import get_all_episodes
        rows = get_all_episodes()
        eps = []
        for row in rows:
            d = str(row.get("episode_date", ""))
            ep = {
                "date": d,
                "title": row.get("title") or d,
                "has_audio": bool(row.get("audio_path")),
                "has_transcript": bool(row.get("transcript_path")),
                "has_script": bool(row.get("script_content") or row.get("script_path")),
                "duration": row.get("duration_minutes", 0) and row["duration_minutes"] * 60,
                "generated_at": row["created_at"].isoformat() if row.get("created_at") and hasattr(row["created_at"], "isoformat") else None,
                "status": row.get("status", "generated"),
            }
            if row.get("share_url"):
                ep["share_url"] = row["share_url"]
            if row.get("transistor_episode_id"):
                ep["transistor_id"] = row["transistor_episode_id"]
            if row.get("published_at") and hasattr(row["published_at"], "isoformat"):
                ep["published_at"] = row["published_at"].isoformat()
                ep["status"] = "published"
            eps.append(ep)
        return eps
    except Exception as exc:
        log.warning("Failed to fetch DB episodes: %s", exc)
        return []


def _fetch_transistor_episodes() -> list[dict]:
    if not TRANSISTOR_API_KEY or not TRANSISTOR_SHOW_ID:
        return []
    try:
        resp = http_requests.get(
            "https://api.transistor.fm/v1/episodes",
            headers={"x-api-key": TRANSISTOR_API_KEY},
            params={"show_id": TRANSISTOR_SHOW_ID, "pagination[per]": 30},
            timeout=10,
        )
        resp.raise_for_status()
        out = []
        for ep in resp.json().get("data", []):
            a = ep["attributes"]
            pub = (a.get("published_at") or a.get("created_at") or "")[:10]
            out.append({
                "transistor_id": ep["id"],
                "date": pub,
                "title": a.get("title", ""),
                "share_url": a.get("share_url", ""),
                "duration": a.get("duration"),
                "status": a.get("status", ""),
                "published_at": a.get("published_at", ""),
            })
        return out
    except Exception:
        return []


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/healthz")
async def healthcheck():
    return JSONResponse({"status": "ok"})


@app.get("/api/schedule")
async def api_schedule():
    job = scheduler.get_job("daily_episode")
    if job and job.next_run_time:
        return JSONResponse({
            "enabled": True,
            "schedule": "Daily at 6:00 AM EST",
            "next_run": job.next_run_time.isoformat(),
        })
    return JSONResponse({"enabled": False})


@app.get("/api/archive")
async def api_archive():
    try:
        from episode_store import get_all_episodes
        episodes = get_all_episodes()
        for ep in episodes:
            for k, v in ep.items():
                if hasattr(v, "isoformat"):
                    ep[k] = v.isoformat()
        return JSONResponse(episodes)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/archive/stats")
async def api_archive_stats():
    try:
        from episode_store import get_summary_stats
        stats = get_summary_stats()
        for k, v in stats.items():
            if hasattr(v, "isoformat"):
                stats[k] = v.isoformat()
            elif isinstance(v, __import__("decimal").Decimal):
                stats[k] = float(v)
        return JSONResponse(stats)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/archive/backfill")
async def api_archive_backfill():
    try:
        from episode_store import archive_episode
        from pathlib import Path
        import re
        output = Path(__file__).parent / "output"
        archived = []
        for f in sorted(output.glob("*_script.json")):
            m = re.match(r"(\d{4}-\d{2}-\d{2})_script\.json", f.name)
            if m:
                from datetime import date as dt_date
                ep_date = dt_date.fromisoformat(m.group(1))
                archive_episode(ep_date)
                archived.append(m.group(1))
        return JSONResponse({"archived": archived})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/api/status")
async def api_status():
    return JSONResponse({k: v for k, v in _job.items() if k != "log"})


@app.get("/api/logs")
async def api_logs():
    return JSONResponse({"lines": _job["log"]})


@app.post("/api/revoice")
async def api_revoice(request: Request):
    """Re-synthesise audio for an existing script with the current voice settings."""
    if _job["running"]:
        return JSONResponse({"error": "A job is already running"}, status_code=409)
    body = await request.json()
    script_date = body.get("date")
    publish = body.get("publish", False)
    if not script_date:
        return JSONResponse({"error": "Missing 'date' field"}, status_code=400)
    script_file = OUTPUT_DIR / f"{script_date}_script.json"
    if not script_file.exists():
        # Try to reconstruct from DB
        try:
            from episode_store import get_episode
            from datetime import date as _date
            row = get_episode(_date.fromisoformat(script_date))
            if row and row.get("script_content"):
                content = row["script_content"]
                import json as _json
                script_file.parent.mkdir(parents=True, exist_ok=True)
                script_file.write_text(
                    _json.dumps(content, indent=2) if isinstance(content, (dict, list)) else str(content)
                )
                log.info("Reconstructed script for %s from DB", script_date)
            else:
                return JSONResponse({"error": f"Script not found for {script_date}"}, status_code=404)
        except Exception as exc:
            log.warning("Could not reconstruct script from DB: %s", exc)
            return JSONResponse({"error": f"Script not found for {script_date}"}, status_code=404)
    import settings as ps
    s = ps.load()
    voice_alex = s.get("voice_alex", "")
    voice_maya = s.get("voice_maya", "")
    all_voices = ps.MALE_VOICES + ps.FEMALE_VOICES
    name_map = {v["id"]: v["name"] for v in all_voices}
    mode = "full" if publish else "no-publish"
    asyncio.create_task(_run_pipeline(mode, from_script=str(script_file)))
    return JSONResponse({
        "status": "started",
        "date": script_date,
        "mode": mode,
        "voice_alex": name_map.get(voice_alex, voice_alex),
        "voice_maya": name_map.get(voice_maya, voice_maya),
    })


@app.post("/api/approve-script")
async def api_approve_script(request: Request):
    if _job["running"]:
        return JSONResponse({"error": "A job is already running"}, status_code=409)
    body = await request.json()
    script_date = body.get("date")
    publish = body.get("publish", False)
    if not script_date:
        return JSONResponse({"error": "Missing 'date' field"}, status_code=400)
    script_file = OUTPUT_DIR / f"{script_date}_script.json"
    if not script_file.exists():
        return JSONResponse({"error": f"Script not found: {script_file.name}"}, status_code=404)
    mode = "full" if publish else "no-publish"
    asyncio.create_task(_run_pipeline(mode, from_script=str(script_file)))
    return JSONResponse({"status": "started", "mode": mode, "from_script": script_file.name})


@app.post("/api/run/{mode}")
async def api_run(mode: str):
    if _job["running"]:
        return JSONResponse({"error": "A job is already running"}, status_code=409)
    if mode not in ("full", "script", "no-publish"):
        return JSONResponse({"error": f"Unknown mode: {mode}"}, status_code=400)
    asyncio.create_task(_run_pipeline(mode))
    return JSONResponse({"status": "started", "mode": mode})


@app.get("/api/story-memory")
async def api_story_memory():
    try:
        from story_memory import get_recent_stories, get_story_count
        stories = get_recent_stories(days=14)
        count = get_story_count(14)
        return JSONResponse({"stories": stories, "count": count})
    except Exception as exc:
        return JSONResponse({"stories": [], "count": 0, "error": str(exc)})


@app.get("/api/story-memory/{date}")
async def api_story_memory_by_date(date: str):
    from datetime import date as dt
    try:
        ep_date = dt.fromisoformat(date)
    except ValueError:
        return JSONResponse({"error": "Invalid date format"}, status_code=400)
    try:
        from story_memory import get_stories_for_date
        stories = get_stories_for_date(ep_date)
        return JSONResponse({"stories": stories, "date": date})
    except Exception as exc:
        return JSONResponse({"stories": [], "date": date, "error": str(exc)}, status_code=500)


@app.get("/api/social-status")
async def api_social_status():
    try:
        from ddgs import DDGS
        available = True
    except ImportError:
        try:
            from duckduckgo_search import DDGS
            available = True
        except ImportError:
            available = False
    return JSONResponse({"configured": available, "method": "web search"})


@app.post("/api/stop")
async def api_stop():
    import os as _os
    import signal as _signal
    global _active_proc
    if not _job["running"] or _active_proc is None:
        return JSONResponse({"error": "No job is currently running"}, status_code=400)
    try:
        pgid = _os.getpgid(_active_proc.pid)
        _os.killpg(pgid, _signal.SIGTERM)
        try:
            await asyncio.wait_for(_active_proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            _os.killpg(pgid, _signal.SIGKILL)
        _broadcast("Job stopped by user\n")
        return JSONResponse({"status": "stopped"})
    except ProcessLookupError:
        return JSONResponse({"error": "Process already finished"}, status_code=400)


@app.get("/api/episodes")
async def api_episodes():
    local = _scan_local_episodes()
    remote = _fetch_transistor_episodes()
    db_eps = _fetch_db_episodes()
    merged: dict[str, dict] = {}
    for ep in db_eps:
        merged[ep["date"]] = ep
    for ep in local:
        d = ep["date"]
        if d in merged:
            merged[d].update(ep)
        else:
            merged[d] = ep
    for ep in remote:
        d = ep["date"]
        if d in merged:
            merged[d].update(ep)
        else:
            merged[d] = ep
    return JSONResponse(sorted(merged.values(), key=lambda e: e["date"], reverse=True))


@app.get("/api/transcript/{date}")
async def api_transcript(date: str):
    path = OUTPUT_DIR / f"{date}_transcript.txt"
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse({"transcript": path.read_text()})


@app.get("/api/files")
async def api_files():
    files = []
    for f in sorted(OUTPUT_DIR.iterdir(), reverse=True):
        if f.is_dir():
            continue
        name = f.name
        if name.endswith("_script.json"):
            ftype = "script"
        elif name.endswith("_transcript.txt"):
            ftype = "transcript"
        elif name.endswith("_description.txt"):
            ftype = "description"
        elif name.endswith(".mp3"):
            ftype = "audio"
        else:
            ftype = "other"
        stat = f.stat()
        files.append({
            "name": name,
            "type": ftype,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })
    return JSONResponse(files)


@app.get("/api/file/{filename}")
async def api_file(filename: str):
    safe = Path(filename).name
    path = OUTPUT_DIR / safe
    if path.exists() and path.is_file():
        if safe.endswith((".txt", ".json")):
            return JSONResponse({"content": path.read_text()})
        return FileResponse(path, filename=safe)
    # Filesystem miss — check DB for script content
    if safe.endswith("_script.json"):
        date_str = safe.replace("_script.json", "")
        try:
            from episode_store import get_episode
            from datetime import date as _date
            row = get_episode(_date.fromisoformat(date_str))
            if row and row.get("script_content"):
                content = row["script_content"]
                import json as _json
                text = _json.dumps(content, indent=2) if isinstance(content, (dict, list)) else str(content)
                return JSONResponse({"content": text})
        except Exception:
            pass
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/api/settings")
async def api_settings():
    data = podcast_settings.load()
    custom = data.get("custom_voices", [])
    male = list(podcast_settings.MALE_VOICES) + [v for v in custom if v.get("gender") == "male"]
    female = list(podcast_settings.FEMALE_VOICES) + [v for v in custom if v.get("gender") == "female"]
    data["_voice_options"] = {"male": male, "female": female}
    data["_model_options"] = podcast_settings.SCRIPT_MODELS
    data["_openai_key_set"] = bool(os.getenv("OPENAI_API_KEY", ""))
    return JSONResponse(data)


@app.post("/api/settings")
async def api_settings_update(request: Request):
    body = await request.json()
    body.pop("_voice_options", None)
    body.pop("_model_options", None)
    updated = podcast_settings.save(body)
    return JSONResponse(updated)


@app.post("/api/custom-voice")
async def api_add_custom_voice(request: Request):
    body = await request.json()
    voice_id = (body.get("id") or "").strip()
    name = (body.get("name") or "").strip()
    gender = body.get("gender", "male")
    if not voice_id:
        return JSONResponse({"error": "Voice ID is required"}, status_code=400)
    if not name:
        name = f"Custom ({voice_id[:8]}…)"
    if gender not in ("male", "female"):
        gender = "male"
    settings = podcast_settings.load()
    custom = settings.get("custom_voices", [])
    if any(v["id"] == voice_id for v in custom):
        return JSONResponse({"error": "Voice ID already exists"}, status_code=409)
    custom.append({"id": voice_id, "name": name, "gender": gender})
    settings["custom_voices"] = custom
    podcast_settings.save(settings)
    return JSONResponse({"status": "added", "voice": {"id": voice_id, "name": name, "gender": gender}})


@app.delete("/api/custom-voice/{voice_id}")
async def api_delete_custom_voice(voice_id: str):
    settings = podcast_settings.load()
    custom = settings.get("custom_voices", [])
    before = len(custom)
    custom = [v for v in custom if v["id"] != voice_id]
    if len(custom) == before:
        return JSONResponse({"error": "Voice not found"}, status_code=404)
    settings["custom_voices"] = custom
    podcast_settings.save(settings)
    return JSONResponse({"status": "deleted"})


@app.get("/api/prompt-sections")
async def api_prompt_sections():
    from script_writer import PROMPT_DEFAULTS
    s = podcast_settings.load()
    custom = s.get("prompt_sections", {})
    sections = {}
    for key in PROMPT_DEFAULTS:
        sections[key] = {
            "value": custom.get(key, PROMPT_DEFAULTS[key]),
            "default": PROMPT_DEFAULTS[key],
            "is_custom": key in custom,
        }
    return JSONResponse(sections)


@app.post("/api/prompt-sections")
async def api_prompt_sections_update(request: Request):
    from script_writer import PROMPT_DEFAULTS
    body = await request.json()
    s = podcast_settings.load()
    custom = s.get("prompt_sections", {})
    for key, value in body.items():
        if key not in PROMPT_DEFAULTS:
            continue
        if not isinstance(value, str):
            continue
        if value.strip() == PROMPT_DEFAULTS[key].strip():
            custom.pop(key, None)
        else:
            custom[key] = value
    s["prompt_sections"] = custom
    podcast_settings.save(s)
    return JSONResponse({"ok": True})


@app.post("/api/prompt-sections/reset")
async def api_prompt_sections_reset(request: Request):
    body = await request.json()
    section = body.get("section")
    s = podcast_settings.load()
    custom = s.get("prompt_sections", {})
    if section:
        custom.pop(section, None)
    else:
        custom.clear()
    s["prompt_sections"] = custom
    podcast_settings.save(s)
    return JSONResponse({"ok": True})


@app.post("/api/preview-script")
async def api_preview_script(request: Request):
    body = await request.json()
    model_key = body.get("model", "claude-opus")
    if model_key not in podcast_settings.VALID_MODEL_IDS:
        return JSONResponse({"error": f"Unknown model: {model_key}"}, status_code=400)

    import asyncio
    from script_writer import generate_script
    from news_fetcher import fetch_daily_news, summarise_for_prompt

    async def _run():
        loop = asyncio.get_event_loop()
        news_data = await loop.run_in_executor(None, fetch_daily_news)
        news_summary = await loop.run_in_executor(None, summarise_for_prompt, news_data)
        try:
            from social_fetcher import fetch_social_reactions, summarise_social_for_prompt
            reactions = await loop.run_in_executor(None, fetch_social_reactions)
            social_summary = await loop.run_in_executor(None, summarise_social_for_prompt, reactions)
            news_summary = news_summary + social_summary
        except Exception:
            pass
        script = await loop.run_in_executor(
            None, lambda: generate_script(news_summary, model_override=model_key)
        )
        return news_summary, script

    import time as _time
    t0 = _time.time()
    try:
        news, script = await _run()
        elapsed = _time.time() - t0

        dialogue = [t for t in script if t["speaker"] in ("ALEX", "MAYA")]
        word_count = sum(len(t["text"].split()) for t in dialogue)

        formatted = []
        for t in script:
            if t["speaker"] == "SFX":
                formatted.append(f'[Sound: {t["text"]}]')
            else:
                formatted.append(f'{t["speaker"]}: {t["text"]}')

        return JSONResponse({
            "model": model_key,
            "script": script,
            "formatted": "\n\n".join(formatted),
            "stats": {
                "turns": len(script),
                "dialogue_turns": len(dialogue),
                "word_count": word_count,
                "elapsed_seconds": round(elapsed, 1),
            },
        })
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/stream")
async def api_stream(request: Request):
    q: asyncio.Queue = asyncio.Queue(maxsize=1000)
    _sse_queues.append(q)
    # Replay existing log to new client
    for line in list(_job["log"]):
        q.put_nowait(line)

    async def generate() -> AsyncGenerator[str, None]:
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(q.get(), timeout=20.0)
                    if item == "__DONE__":
                        yield "data: __DONE__\n\n"
                        break
                    yield f"data: {json.dumps(item)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            if q in _sse_queues:
                _sse_queues.remove(q)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Dashboard HTML ─────────────────────────────────────────────────────────────
LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mind the Gap — Login</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0c0f1a; --surface: rgba(255,255,255,.04); --border: rgba(255,255,255,.08);
    --text: #f0f2f5; --muted: #8b92a5; --accent: #a78bfa; --accent-dim: rgba(167,139,250,.12);
    --green: #34d399; --red: #f87171;
    --font: 'Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: var(--font);
         min-height: 100vh; display: flex; align-items: center; justify-content: center;
         background-image: radial-gradient(ellipse at 50% 0%, rgba(167,139,250,.08) 0%, transparent 60%),
                           radial-gradient(ellipse at 80% 100%, rgba(52,211,153,.05) 0%, transparent 50%); }
  .login-card { background: rgba(255,255,255,.03); border: 1px solid var(--border);
                border-radius: 20px; padding: 48px 40px; width: 400px; max-width: 92%;
                backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                box-shadow: 0 8px 32px rgba(0,0,0,.3), inset 0 1px 0 rgba(255,255,255,.05); }
  .logo { display: flex; align-items: center; gap: 12px; font-size: 22px;
          font-weight: 700; margin-bottom: 6px; justify-content: center;
          letter-spacing: -0.02em; }
  .logo svg { color: var(--accent); filter: drop-shadow(0 0 8px rgba(167,139,250,.4)); }
  .subtitle { text-align: center; font-size: 14px; color: var(--muted); margin-bottom: 32px;
              font-weight: 400; }
  label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 8px; font-weight: 500; }
  .input-wrap { position: relative; }
  .input-wrap svg { position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
                    color: var(--muted); pointer-events: none; }
  input[type="password"] { width: 100%; padding: 12px 14px 12px 42px; border-radius: 12px;
         border: 1px solid var(--border); background: rgba(0,0,0,.3); color: var(--text);
         font-size: 14px; font-family: var(--font); outline: none; transition: all .2s; }
  input[type="password"]:focus { border-color: var(--accent);
         box-shadow: 0 0 0 3px var(--accent-dim); }
  .btn { width: 100%; padding: 12px; border-radius: 12px; border: none;
         background: linear-gradient(135deg, #7c3aed, #a78bfa); color: #fff;
         font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 20px;
         transition: all .2s; font-family: var(--font); letter-spacing: .01em; }
  .btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(124,58,237,.35); }
  .btn:active { transform: translateY(0); }
  .error { background: rgba(248,113,113,.08); border: 1px solid rgba(248,113,113,.2);
           color: var(--red); padding: 10px 14px; border-radius: 10px; font-size: 13px;
           margin-bottom: 16px; text-align: center; }
  .footer { text-align: center; margin-top: 24px; font-size: 12px; color: var(--muted); opacity: .6; }
</style>
</head>
<body>
<div class="login-card">
  <div class="logo">
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="22"/>
      <line x1="8" y1="22" x2="16" y2="22"/>
    </svg>
    Mind the Gap
  </div>
  <div class="subtitle">Podcast Control Panel</div>
  <!--ERROR-->
  <form method="POST" action="/login">
    <label for="password">Password</label>
    <div class="input-wrap">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      </svg>
      <input type="password" id="password" name="password" placeholder="Enter your password" autofocus required autocomplete="current-password">
    </div>
    <button type="submit" class="btn">Sign In</button>
  </form>
  <div class="footer">Protected access</div>
</div>
</body>
</html>"""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mind the Gap — Control Panel</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:       #0c0f1a;
    --surface:  rgba(255,255,255,.03);
    --surface-s: #141829;
    --border:   rgba(255,255,255,.07);
    --text:     #f0f2f5;
    --muted:    #6b7280;
    --green:    #34d399;
    --green-dim:rgba(52,211,153,.1);
    --red:      #f87171;
    --red-dim:  rgba(248,113,113,.1);
    --yellow:   #fbbf24;
    --blue:     #60a5fa;
    --purple:   #a78bfa;
    --accent:   #a78bfa;
    --font:     'Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    --mono:     "SF Mono","Fira Code",Consolas,monospace;
    --radius:   14px;
    --radius-sm:10px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: var(--font);
         font-size: 14px; line-height: 1.6; min-height: 100vh;
         background-image: radial-gradient(ellipse at 30% 0%, rgba(167,139,250,.06) 0%, transparent 50%),
                           radial-gradient(ellipse at 80% 100%, rgba(52,211,153,.03) 0%, transparent 40%); }

  .app { max-width: 1240px; margin: 0 auto; padding: 0 24px 48px; }

  header { display: flex; align-items: center; justify-content: space-between;
           padding: 20px 0 18px; margin-bottom: 28px;
           border-bottom: 1px solid var(--border); }
  .logo { display: flex; align-items: center; gap: 12px; font-size: 18px;
          font-weight: 700; letter-spacing: -0.02em; }
  .logo svg { color: var(--accent); filter: drop-shadow(0 0 6px rgba(167,139,250,.3)); }
  .header-right { display: flex; align-items: center; gap: 16px; }
  .logout-btn { font-size: 12px; color: var(--muted); background: none; padding: 6px 14px;
                border: 1px solid var(--border); border-radius: 8px; cursor: pointer;
                font-family: var(--font); transition: all .2s; font-weight: 500; }
  .logout-btn:hover { color: var(--text); background: rgba(255,255,255,.05); border-color: rgba(255,255,255,.12); }

  .grid { display: grid; grid-template-columns: 320px 1fr; gap: 20px; margin-bottom: 24px; }
  @media (max-width: 740px) { .grid { grid-template-columns: 1fr; } }

  .card { background: var(--surface); border: 1px solid var(--border);
          border-radius: var(--radius); padding: 22px;
          backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }
  .card-title { font-size: 11px; font-weight: 600; letter-spacing: .1em;
                text-transform: uppercase; color: var(--muted); margin-bottom: 16px; }

  .section-label { font-size: 12px; font-weight: 600; color: var(--accent);
                   margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
  .section-label svg { width: 14px; height: 14px; opacity: .7; }

  .status-badge { display: inline-flex; align-items: center; gap: 7px;
                  font-size: 13px; font-weight: 500; padding: 5px 14px;
                  border-radius: 20px; margin-bottom: 16px; }
  .status-badge.idle    { background: var(--green-dim); color: var(--green); }
  .status-badge.running { background: rgba(96,165,250,.1); color: var(--blue); }
  .status-badge.failed  { background: var(--red-dim); color: var(--red); }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .dot.pulse { animation: pulse 1.4s ease-in-out infinite; }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.25; } }

  .btn-group { display: flex; flex-direction: column; gap: 8px; }
  .btn { width: 100%; padding: 10px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border);
         font-size: 13px; font-weight: 500; cursor: pointer; display: flex;
         align-items: center; gap: 10px; transition: all .2s; background: var(--surface);
         color: var(--text); text-align: left; font-family: var(--font); }
  .btn:hover { background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.12);
               transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,.2); }
  .btn:active { transform: translateY(0); box-shadow: none; }
  .btn.primary { background: linear-gradient(135deg, #059669, #34d399); border-color: transparent; color: #fff; }
  .btn.primary:hover { box-shadow: 0 4px 16px rgba(52,211,153,.25); }
  .btn:disabled { opacity: .4; cursor: not-allowed; transform: none !important; box-shadow: none !important; }
  .btn-icon { font-size: 16px; min-width: 20px; }

  .meta-row { display: flex; justify-content: space-between; font-size: 12px;
              color: var(--muted); padding: 7px 0; border-bottom: 1px solid var(--border); }
  .meta-row:last-child { border-bottom: none; }
  .meta-row span:last-child { color: var(--text); text-align: right; max-width: 60%; word-break: break-all; font-weight: 500; }

  .console-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .console { background: rgba(0,0,0,.35); border: 1px solid var(--border); border-radius: var(--radius-sm);
             height: 320px; overflow-y: auto; padding: 14px 16px; font-family: var(--mono);
             font-size: 12px; line-height: 1.8; scroll-behavior: smooth; }
  .console::-webkit-scrollbar { width: 5px; }
  .console::-webkit-scrollbar-track { background: transparent; }
  .console::-webkit-scrollbar-thumb { background: rgba(255,255,255,.1); border-radius: 3px; }
  .console::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,.18); }
  .log-line { white-space: pre-wrap; word-break: break-all; }
  .log-line.info  { color: var(--muted); }
  .log-line.warn  { color: var(--yellow); }
  .log-line.error { color: var(--red); }
  .log-line.step  { color: var(--blue); font-weight: 600; }
  .log-line.ok    { color: var(--green); font-weight: 600; }
  .log-line.fail  { color: var(--red); font-weight: 600; }
  .log-line.start { color: var(--purple); font-weight: 600; }

  .ep-table { width: 100%; border-collapse: separate; border-spacing: 0; }
  .ep-table th { font-size: 10px; font-weight: 600; letter-spacing: .08em;
                 text-transform: uppercase; color: var(--muted); padding: 8px 12px;
                 border-bottom: 1px solid var(--border); text-align: left; }
  .ep-table td { padding: 12px 12px; border-bottom: 1px solid var(--border);
                 font-size: 13px; vertical-align: middle; }
  .ep-table tr:last-child td { border-bottom: none; }
  .ep-table tbody tr { transition: background .15s; }
  .ep-table tbody tr:hover td { background: rgba(255,255,255,.03); }
  .ep-title { font-weight: 500; color: var(--text); }
  .ep-date  { color: var(--muted); white-space: nowrap; }
  .ep-dur   { color: var(--muted); white-space: nowrap; font-family: var(--mono); font-size: 12px; }
  .ep-actions { display: flex; gap: 6px; justify-content: flex-end; }
  .pill { display: inline-flex; align-items: center; gap: 4px; padding: 4px 12px;
          border-radius: 8px; font-size: 12px; border: 1px solid; cursor: pointer;
          text-decoration: none; font-weight: 500; transition: all .2s; font-family: var(--font); }
  .pill.listen { color: var(--green); border-color: rgba(52,211,153,.2); background: rgba(52,211,153,.06); }
  .pill.listen:hover { background: rgba(52,211,153,.12); transform: translateY(-1px); }
  .pill.transcript { color: var(--blue); border-color: rgba(96,165,250,.2); background: rgba(96,165,250,.06); }
  .pill.transcript:hover { background: rgba(96,165,250,.12); transform: translateY(-1px); }
  .pill.script { color: var(--purple); border-color: rgba(167,139,250,.2); background: rgba(167,139,250,.06); }
  .pill.script:hover { background: rgba(167,139,250,.12); transform: translateY(-1px); }
  .pill.draft { color: var(--yellow); border-color: rgba(251,191,36,.2); background: rgba(251,191,36,.06); }
  .pill.memory { color: var(--accent); border-color: rgba(167,139,250,.2); background: rgba(167,139,250,.06); }
  .pill.memory:hover { background: rgba(167,139,250,.12); transform: translateY(-1px); }
  .pill.memory.active { background: rgba(167,139,250,.15); border-color: rgba(167,139,250,.35); }

  .memory-panel { display: none; padding: 16px 20px; background: rgba(0,0,0,.2);
                  border-top: 1px solid var(--border); }
  .memory-panel.open { display: block; }
  .memory-story { padding: 10px 14px; border-radius: var(--radius-sm); margin-bottom: 8px;
                  background: var(--surface); border: 1px solid var(--border);
                  transition: all .15s; }
  .memory-story:last-child { margin-bottom: 0; }
  .memory-story:hover { border-color: rgba(255,255,255,.1); }
  .memory-story-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
  .memory-cat { font-size: 10px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase;
                padding: 2px 8px; border-radius: 4px; white-space: nowrap; }
  .memory-cat.toronto_canada { background: rgba(52,211,153,.1); color: var(--green); }
  .memory-cat.global_macro { background: rgba(96,165,250,.1); color: var(--blue); }
  .memory-cat.ai_tech { background: rgba(251,191,36,.1); color: var(--yellow); }
  .memory-cat.behavioural_spirituality { background: rgba(167,139,250,.1); color: var(--accent); }
  .memory-cat.general { background: rgba(255,255,255,.05); color: var(--muted); }
  .memory-headline { font-size: 13px; font-weight: 600; color: var(--text); flex: 1; }
  .memory-summary { font-size: 12px; color: var(--muted); line-height: 1.5; margin-top: 4px; }
  .memory-entities { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 6px; }
  .memory-entity { font-size: 10px; padding: 1px 7px; border-radius: 4px; font-weight: 500;
                   background: rgba(255,255,255,.04); color: var(--muted); border: 1px solid var(--border); }
  .memory-continuation { font-size: 10px; padding: 1px 7px; border-radius: 4px; font-weight: 600;
                         background: rgba(96,165,250,.1); color: var(--blue); }
  .memory-empty { font-size: 12px; color: var(--muted); text-align: center; padding: 16px 0; }
  .ep-ts { color: var(--muted); font-size: 11px; font-family: var(--mono); white-space: nowrap; }
  .ep-table tbody tr.ep-row:nth-child(4n+1) td { background: transparent; }
  .ep-table tbody tr.ep-row:nth-child(4n+3) td { background: rgba(255,255,255,.01); }
  .ep-table tbody tr.ep-row:hover td { background: rgba(255,255,255,.04) !important; }

  .file-group-title { font-size: 12px; font-weight: 600; color: var(--accent); padding: 12px 0 6px;
                      border-bottom: 1px solid var(--border); margin-top: 8px; }
  .file-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px;
              border-bottom: 1px solid var(--border); font-size: 13px; transition: background .15s; border-radius: 6px; }
  .file-row:last-child { border-bottom: none; }
  .file-row:hover { background: rgba(255,255,255,.03); }
  .file-name { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
  .file-name span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .file-icon { font-size: 16px; min-width: 20px; }
  .file-meta { color: var(--muted); font-size: 12px; white-space: nowrap; margin-left: 12px; }
  .file-actions { display: flex; gap: 6px; margin-left: 12px; }

  .badge-pub   { color: var(--green); font-size: 11px; font-weight: 500; }
  .badge-draft { color: var(--yellow); font-size: 11px; font-weight: 500; }

  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
  .stat-card { background: var(--surface); border: 1px solid var(--border);
               border-radius: var(--radius); padding: 20px 22px; position: relative; overflow: hidden;
               backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: all .2s; }
  .stat-card:hover { border-color: rgba(255,255,255,.1); transform: translateY(-2px);
                     box-shadow: 0 4px 16px rgba(0,0,0,.2); }
  .stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0;
                       height: 3px; border-radius: var(--radius) var(--radius) 0 0; }
  .stat-card:nth-child(1)::before { background: linear-gradient(90deg, #059669, #34d399); }
  .stat-card:nth-child(2)::before { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
  .stat-card:nth-child(3)::before { background: linear-gradient(90deg, #2563eb, #60a5fa); }
  .stat-val { font-size: 28px; font-weight: 700; line-height: 1.2; letter-spacing: -0.02em; }
  .stat-lbl { font-size: 12px; color: var(--muted); margin-top: 4px; font-weight: 500; }
  .stat-val.green  { color: var(--green); }
  .stat-val.purple { color: var(--purple); }
  .stat-val.blue   { color: var(--blue); }

  .modal-bg { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.6);
              backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
              z-index: 100; align-items: center; justify-content: center; }
  .modal-bg.open { display: flex; }
  .modal { background: var(--surface-s); border: 1px solid var(--border); border-radius: 16px;
           padding: 28px; max-width: 700px; width: 92%; max-height: 82vh; display: flex;
           flex-direction: column; box-shadow: 0 16px 48px rgba(0,0,0,.4); }
  .modal-header { display: flex; justify-content: space-between; align-items: center;
                  margin-bottom: 16px; }
  .modal-title { font-size: 16px; font-weight: 600; letter-spacing: -0.01em; }
  .modal-close { background: none; border: 1px solid var(--border); color: var(--muted); cursor: pointer;
                 font-size: 14px; padding: 4px 10px; border-radius: 8px; transition: all .15s; font-family: var(--font); }
  .modal-close:hover { background: rgba(255,255,255,.05); color: var(--text); }
  .modal-body { overflow-y: auto; flex: 1; font-size: 13px; line-height: 1.8;
                white-space: pre-wrap; font-family: var(--mono); color: var(--muted); }
  .modal-body strong { color: var(--text); }

  .slider-row { margin-bottom: 14px; }
  .slider-label { display: flex; justify-content: space-between; font-size: 13px;
                  color: var(--text); margin-bottom: 6px; font-weight: 500; }
  .slider-val { color: var(--accent); font-weight: 600; font-family: var(--mono); min-width: 30px; text-align: right; }
  .setting-slider { width: 100%; height: 5px; -webkit-appearance: none; appearance: none;
                    background: rgba(255,255,255,.08); border-radius: 3px; outline: none; cursor: pointer;
                    transition: background .15s; }
  .setting-slider:hover { background: rgba(255,255,255,.12); }
  .setting-slider::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px;
                                          border-radius: 50%; background: var(--accent); cursor: pointer;
                                          border: 3px solid var(--surface-s);
                                          box-shadow: 0 0 0 1px rgba(167,139,250,.3), 0 2px 4px rgba(0,0,0,.3); transition: all .15s; }
  .setting-slider::-webkit-slider-thumb:hover { transform: scale(1.15);
                                                box-shadow: 0 0 0 2px rgba(167,139,250,.4), 0 2px 8px rgba(0,0,0,.3); }
  .setting-slider::-moz-range-thumb { width: 16px; height: 16px; border-radius: 50%;
                                      background: var(--accent); cursor: pointer; border: 3px solid var(--surface-s); }

  .setting-select { width: 100%; padding: 9px 12px; border-radius: var(--radius-sm); border: 1px solid var(--border);
                    background: rgba(0,0,0,.25); color: var(--text); font-size: 13px; font-family: var(--font);
                    cursor: pointer; outline: none; transition: all .2s; font-weight: 500; }
  .setting-select:hover { border-color: rgba(255,255,255,.12); }
  .setting-select:focus { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(167,139,250,.15); }

  .prompt-section { margin-bottom: 18px; }
  .prompt-section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .prompt-section-label { font-size: 13px; font-weight: 600; color: var(--text); }
  .prompt-section-badge { font-size: 10px; padding: 3px 8px; border-radius: 6px; font-weight: 600; letter-spacing: .02em; }
  .prompt-section-badge.custom { background: rgba(52,211,153,.1); color: var(--green); }
  .prompt-section-badge.default { background: rgba(255,255,255,.04); color: var(--muted); }
  .prompt-textarea { width: 100%; min-height: 130px; padding: 14px 16px; border-radius: var(--radius-sm);
    border: 1px solid var(--border); background: rgba(0,0,0,.25); color: var(--text); font-size: 12px;
    font-family: var(--mono); line-height: 1.6; resize: vertical; outline: none; transition: all .2s; }
  .prompt-textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(167,139,250,.12); }
  .prompt-actions { display: flex; gap: 8px; margin-top: 6px; justify-content: flex-end; }
  .collapse-toggle { cursor: pointer; user-select: none; }
  .collapse-toggle .arrow { display: inline-block; transition: transform 0.2s ease; font-size: 10px; margin-right: 8px; }
  .collapse-toggle.open .arrow { transform: rotate(90deg); }

  .btn.danger { background: var(--red-dim); border-color: rgba(248,113,113,.2); color: var(--red); }
  .btn.danger:hover { background: rgba(248,113,113,.15); border-color: rgba(248,113,113,.3); }

  @keyframes savePulse { 0% { opacity:1; } 50% { opacity:.5; } 100% { opacity:1; } }
  .saving { animation: savePulse .8s ease-in-out infinite; color: var(--yellow) !important; }
  .saved { color: var(--green) !important; }

  .footer { text-align: center; padding: 24px 0 12px; font-size: 12px; color: var(--muted);
            border-top: 1px solid var(--border); margin-top: 32px; opacity: .5; }

  .empty { color: var(--muted); font-size: 13px; padding: 28px 0; text-align: center; }
  .small-btn { background: rgba(255,255,255,.04); border: 1px solid var(--border); color: var(--muted);
               border-radius: 8px; padding: 5px 12px; font-size: 12px; cursor: pointer;
               font-family: var(--font); transition: all .2s; font-weight: 500; }
  .small-btn:hover { background: rgba(255,255,255,.08); color: var(--text); border-color: rgba(255,255,255,.12); }

  .tab-bar { display: flex; gap: 4px; margin-bottom: 24px; background: var(--surface);
             border: 1px solid var(--border); border-radius: var(--radius); padding: 4px;
             backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }
  .tab-btn { flex: 1; padding: 11px 18px; border-radius: var(--radius-sm); border: none;
             background: transparent; color: var(--muted); font-size: 13px; font-weight: 600;
             cursor: pointer; font-family: var(--font); transition: all .2s;
             display: flex; align-items: center; justify-content: center; gap: 8px;
             letter-spacing: 0.01em; }
  .tab-btn:hover { color: var(--text); background: rgba(255,255,255,.04); }
  .tab-btn.active { background: rgba(167,139,250,.12); color: var(--accent);
                    box-shadow: 0 1px 4px rgba(0,0,0,.15); }
  .tab-btn svg { width: 15px; height: 15px; opacity: .7; }
  .tab-btn.active svg { opacity: 1; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important; }
  }
</style>
</head>
<body>
<div class="app">

  <header>
    <div class="logo">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
        <line x1="12" y1="19" x2="12" y2="22"/>
        <line x1="8" y1="22" x2="16" y2="22"/>
      </svg>
      Mind the Gap
    </div>
    <div class="header-right">
      <div id="header-status" style="font-size:12px;color:var(--muted);font-weight:500">Loading...</div>
      <form method="POST" action="/logout" style="margin:0">
        <button type="submit" class="logout-btn">Logout</button>
      </form>
    </div>
  </header>

  <div class="tab-bar" role="tablist" aria-label="Dashboard sections">
    <button class="tab-btn active" onclick="switchTab('run')" id="tab-btn-run" role="tab" aria-selected="true" aria-controls="panel-run" tabindex="0">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
      Run
    </button>
    <button class="tab-btn" onclick="switchTab('configure')" id="tab-btn-configure" role="tab" aria-selected="false" aria-controls="panel-configure" tabindex="-1">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      Configure
    </button>
    <button class="tab-btn" onclick="switchTab('history')" id="tab-btn-history" role="tab" aria-selected="false" aria-controls="panel-history" tabindex="-1">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      Historical Runs
    </button>
  </div>

  <div class="tab-panel active" id="panel-run" role="tabpanel" aria-labelledby="tab-btn-run">

    <div class="stats">
      <div class="stat-card">
        <div class="stat-val green" id="stat-total">--</div>
        <div class="stat-lbl">Episodes published</div>
      </div>
      <div class="stat-card">
        <div class="stat-val purple" id="stat-last">--</div>
        <div class="stat-lbl">Last episode</div>
      </div>
      <div class="stat-card">
        <div class="stat-val blue" id="stat-runtime">--</div>
        <div class="stat-lbl">Avg runtime</div>
      </div>
    </div>

    <div class="grid">

      <div class="card">
        <div class="card-title">Job Controls</div>
        <div id="status-badge" class="status-badge idle">
          <div class="dot" id="status-dot"></div>
          <span id="status-text">Idle</span>
        </div>

        <div id="last-run-info" style="margin-bottom:16px"></div>

        <div id="review-banner" style="display:none;margin-bottom:16px;padding:14px 18px;background:rgba(250,204,21,.08);border:1px solid rgba(250,204,21,.25);border-radius:var(--radius);cursor:pointer" onclick="openPendingReview()">
          <div style="display:flex;align-items:center;gap:10px">
            <span style="font-size:20px">📄</span>
            <div>
              <div style="font-weight:600;color:var(--yellow)">Script ready for review</div>
              <div style="font-size:12px;color:var(--muted);margin-top:2px">Tap to read the transcript and approve</div>
            </div>
            <span style="margin-left:auto;color:var(--muted);font-size:18px">&#8250;</span>
          </div>
        </div>

        <div class="btn-group">
          <button class="btn primary" id="btn-full" onclick="runJob('full')">
            <span class="btn-icon">▶</span>
            <div>
              <div style="font-weight:600">Run full episode</div>
              <div style="font-size:11px;font-weight:400;opacity:.55;margin-top:2px">Fetch news, script, audio, publish</div>
            </div>
          </button>
          <button class="btn" id="btn-script" onclick="runJob('script')">
            <span class="btn-icon">📝</span>
            <div>
              <div style="font-weight:600">Script preview only</div>
              <div style="font-size:11px;font-weight:400;opacity:.55;margin-top:2px">Generate script, skip audio + publish</div>
            </div>
          </button>
          <button class="btn" id="btn-nopub" onclick="runJob('no-publish')">
            <span class="btn-icon">🔇</span>
            <div>
              <div style="font-weight:600">Audio, no publish</div>
              <div style="font-size:11px;font-weight:400;opacity:.55;margin-top:2px">Generate audio but don't push to Transistor</div>
            </div>
          </button>
          <button class="btn danger" id="btn-stop" onclick="stopJob()" style="display:none">
            <span class="btn-icon">■</span>
            <div>
              <div style="font-weight:600">Stop current job</div>
              <div style="font-size:11px;font-weight:400;opacity:.55;margin-top:2px">Terminate the running pipeline</div>
            </div>
          </button>
        </div>

        <div style="margin-top:20px">
          <div class="card-title">Configuration</div>
          <div class="meta-row"><span>Show</span><span>Mind the Gap</span></div>
          <div class="meta-row"><span>Hosts</span><span>Alex + Maya</span></div>
          <div class="meta-row"><span>Social Pulse</span><span id="social-status" style="color:var(--green)">Active</span></div>
          <div class="meta-row"><span>Model</span><span>Claude Opus 4.6</span></div>
          <div class="meta-row"><span>TTS</span><span>ElevenLabs v2</span></div>
          <div class="meta-row"><span>Target</span><span>~10-20 min</span></div>
          <div class="meta-row"><span>Schedule</span><span id="schedule-status" style="color:var(--green)">Daily 6:00 AM EST</span></div>
        </div>
      </div>

      <div class="card">
        <div class="console-header">
          <div class="card-title" style="margin:0">Live Console</div>
          <div style="display:flex;gap:8px">
            <button class="small-btn" id="btn-autoscroll" onclick="toggleAutoscroll()">Auto-scroll: ON</button>
            <button class="small-btn" onclick="clearConsole()">Clear</button>
          </div>
        </div>
        <div class="console" id="console">
          <div class="log-line info">Ready. Click a run button to start.</div>
        </div>
      </div>
    </div>

  </div>

  <div class="tab-panel" id="panel-configure" role="tabpanel" aria-labelledby="tab-btn-configure" aria-hidden="true">

  <div class="card" style="margin-bottom:24px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px">
      <div class="card-title" style="margin:0">Editorial Controls</div>
      <span id="settings-status" style="font-size:11px;color:var(--muted);font-weight:500"></span>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:28px">
      <div>
        <div class="section-label">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          Content Mix
        </div>

        <div class="slider-row">
          <div class="slider-label">
            <span>Stories to weave</span>
            <span class="slider-val" id="val-story_count">1</span>
          </div>
          <input type="range" class="setting-slider" id="s-story_count" min="1" max="8" step="1" value="1">
        </div>

        <div class="slider-row">
          <div class="slider-label">
            <span>Behavioral econ concepts</span>
            <span class="slider-val" id="val-behavioral_concepts">2</span>
          </div>
          <input type="range" class="setting-slider" id="s-behavioral_concepts" min="0" max="5" step="1" value="2">
        </div>

        <div class="slider-row">
          <div class="slider-label">
            <span>Spirituality concepts</span>
            <span class="slider-val" id="val-spirituality_concepts">1</span>
          </div>
          <input type="range" class="setting-slider" id="s-spirituality_concepts" min="0" max="5" step="1" value="1">
        </div>
      </div>

      <div>
        <div class="section-label">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
          Geographic Focus
        </div>

        <div class="slider-row">
          <div class="slider-label">
            <span>Toronto / Local</span>
            <span class="slider-val" id="val-geo_toronto_pct">25%</span>
          </div>
          <input type="range" class="setting-slider geo-slider" id="s-geo_toronto_pct" min="0" max="100" step="5" value="25">
        </div>

        <div class="slider-row">
          <div class="slider-label">
            <span>Canada</span>
            <span class="slider-val" id="val-geo_canada_pct">25%</span>
          </div>
          <input type="range" class="setting-slider geo-slider" id="s-geo_canada_pct" min="0" max="100" step="5" value="25">
        </div>

        <div class="slider-row">
          <div class="slider-label">
            <span>AI / Tech</span>
            <span class="slider-val" id="val-geo_ai_tech_pct">25%</span>
          </div>
          <input type="range" class="setting-slider geo-slider" id="s-geo_ai_tech_pct" min="0" max="100" step="5" value="25">
        </div>

        <div class="slider-row">
          <div class="slider-label">
            <span>World / Global</span>
            <span class="slider-val" id="val-geo_world_pct">25%</span>
          </div>
          <input type="range" class="setting-slider geo-slider" id="s-geo_world_pct" min="0" max="100" step="5" value="25">
        </div>

        <div id="geo-bar" style="display:flex;height:6px;border-radius:6px;overflow:hidden;margin-top:8px;gap:2px">
          <div id="gbar-toronto" style="background:var(--green);width:25%;border-radius:3px;transition:width .3s"></div>
          <div id="gbar-canada" style="background:var(--blue);width:25%;border-radius:3px;transition:width .3s"></div>
          <div id="gbar-ai-tech" style="background:var(--yellow);width:25%;border-radius:3px;transition:width .3s"></div>
          <div id="gbar-world" style="background:var(--purple);width:25%;border-radius:3px;transition:width .3s"></div>
        </div>
        <div style="display:flex;gap:14px;margin-top:6px;font-size:10px;color:var(--muted);font-weight:500">
          <span style="color:var(--green)">&#9679; Toronto</span>
          <span style="color:var(--blue)">&#9679; Canada</span>
          <span style="color:var(--yellow)">&#9679; AI/Tech</span>
          <span style="color:var(--purple)">&#9679; World</span>
        </div>
      </div>
    </div>

    <div style="margin-top:22px;border-top:1px solid var(--border);padding-top:18px">
      <div class="section-label">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        Voice Selection
      </div>
      <div style="margin-bottom:16px">
        <label style="font-size:12px;color:var(--muted);display:block;margin-bottom:6px;font-weight:500">TTS Provider</label>
        <select id="s-tts_provider" class="setting-select" onchange="onTtsProviderChange()">
          <option value="elevenlabs">ElevenLabs (GenFM)</option>
          <option value="openai">OpenAI TTS</option>
        </select>
        <div id="tts-provider-hint" style="margin-top:6px;font-size:11px;color:var(--muted);opacity:.7"></div>
      </div>
      <div id="elevenlabs-voice-config">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
          <div>
            <label style="font-size:12px;color:var(--muted);display:block;margin-bottom:6px;font-weight:500">Alex (Male)</label>
            <select id="s-voice_alex" class="setting-select">
              <option value="">Loading...</option>
            </select>
          </div>
          <div>
            <label style="font-size:12px;color:var(--muted);display:block;margin-bottom:6px;font-weight:500">Maya (Female)</label>
            <select id="s-voice_maya" class="setting-select">
              <option value="">Loading...</option>
            </select>
          </div>
        </div>
      </div>
      <div id="openai-voice-config" style="display:none">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
          <div style="background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:10px;padding:12px 14px">
            <div style="font-size:12px;color:var(--muted);margin-bottom:4px;font-weight:500">Alex (Male) — Onyx</div>
            <textarea id="s-voice_direction_alex" class="setting-textarea" rows="4" style="width:100%;margin-top:6px;background:rgba(0,0,0,.25);border:1px solid var(--border);border-radius:8px;padding:8px 10px;color:var(--text);font-size:12px;line-height:1.5;resize:vertical;font-family:inherit" placeholder="Voice direction for Alex..."></textarea>
          </div>
          <div style="background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:10px;padding:12px 14px">
            <div style="font-size:12px;color:var(--muted);margin-bottom:4px;font-weight:500">Maya (Female) — Nova</div>
            <textarea id="s-voice_direction_maya" class="setting-textarea" rows="4" style="width:100%;margin-top:6px;background:rgba(0,0,0,.25);border:1px solid var(--border);border-radius:8px;padding:8px 10px;color:var(--text);font-size:12px;line-height:1.5;resize:vertical;font-family:inherit" placeholder="Voice direction for Maya..."></textarea>
          </div>
        </div>
        <div style="font-size:11px;color:var(--muted);margin-top:8px;opacity:.7">Voice directions tell the TTS model <em>how</em> to speak — personality, energy, pacing. Edit freely; changes auto-save.</div>
      </div>
      <div id="custom-voices-list" style="margin-top:12px"></div>
      <details style="margin-top:14px">
        <summary style="cursor:pointer;font-size:12px;color:var(--accent);font-weight:500;user-select:none">+ Add Custom ElevenLabs Voice</summary>
        <div style="margin-top:10px;background:rgba(255,255,255,.03);border:1px solid var(--border);border-radius:10px;padding:14px 16px">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
            <div>
              <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">ElevenLabs Voice ID</label>
              <input id="cv-id" class="setting-input" placeholder="e.g. xKhbyU7E3bC6T89Kn26c" style="font-family:monospace;font-size:12px">
            </div>
            <div>
              <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Display Name</label>
              <input id="cv-name" class="setting-input" placeholder="e.g. My Custom Voice">
            </div>
          </div>
          <div style="display:flex;gap:10px;align-items:center">
            <select id="cv-gender" class="setting-select" style="width:auto;min-width:120px">
              <option value="male">Male (Alex)</option>
              <option value="female">Female (Maya)</option>
            </select>
            <button class="small-btn" onclick="addCustomVoice()" style="white-space:nowrap">Add Voice</button>
            <span id="cv-status" style="font-size:11px;color:var(--muted)"></span>
          </div>
        </div>
      </details>
    </div>

    <div style="margin-top:22px;border-top:1px solid var(--border);padding-top:18px">
      <div class="section-label">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Playback Speed
      </div>
      <div class="slider-row">
        <div class="slider-label">
          <span>Dialogue speed</span>
          <span class="slider-val" id="val-audio_speed">110%</span>
        </div>
        <input type="range" class="setting-slider" id="s-audio_speed" min="80" max="130" step="5" value="110">
      </div>
      <div style="margin-top:4px;font-size:11px;color:var(--muted);opacity:.7">
        100% = natural speed. Higher values speed up the dialogue while keeping pitch natural.
      </div>
    </div>

    <div style="margin-top:22px;border-top:1px solid var(--border);padding-top:18px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
        <div class="section-label" style="margin-bottom:0">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
          Script Model
        </div>
        <button class="small-btn" id="btn-compare" onclick="openCompare()">Compare Models</button>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
        <div>
          <label style="font-size:12px;color:var(--muted);display:block;margin-bottom:6px;font-weight:500">Primary Model</label>
          <select id="s-script_model" class="setting-select" onchange="onModelChange()">
            <option value="">Loading...</option>
          </select>
        </div>
        <div>
          <label style="font-size:12px;color:var(--muted);display:block;margin-bottom:6px;font-weight:500">Fallback Model</label>
          <select id="s-fallback_model" class="setting-select" onchange="onModelChange()">
            <option value="">Loading...</option>
          </select>
        </div>
      </div>
      <div style="margin-top:8px;font-size:11px;color:var(--muted);opacity:.7">
        If the primary model fails after retries, the pipeline auto-switches to the fallback.
      </div>
    </div>

    <div style="margin-top:22px;border-top:1px solid var(--border);padding-top:18px">
      <div class="section-label">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        Estimated Cost per Episode
      </div>
      <div id="cost-panel" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px">
        <div style="background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:14px;text-align:center">
          <div id="cost-llm-label" style="font-size:10px;color:var(--muted);margin-bottom:6px;font-weight:500">LLM (Script)</div>
          <div id="cost-anthropic" style="font-size:18px;font-weight:700;color:var(--yellow)">$0.00</div>
          <div id="cost-anthropic-detail" style="font-size:9px;color:var(--muted);margin-top:4px"></div>
        </div>
        <div style="background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:14px;text-align:center">
          <div id="cost-elevenlabs-label" style="font-size:10px;color:var(--muted);margin-bottom:6px;font-weight:500">ElevenLabs (Audio)</div>
          <div id="cost-elevenlabs" style="font-size:18px;font-weight:700;color:var(--blue)">$0.00</div>
          <div id="cost-elevenlabs-detail" style="font-size:9px;color:var(--muted);margin-top:4px"></div>
        </div>
        <div style="background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:14px;text-align:center">
          <div style="font-size:10px;color:var(--muted);margin-bottom:6px;font-weight:500">Replit Hosting</div>
          <div id="cost-hosting" style="font-size:18px;font-weight:700;color:var(--green)">$0.23</div>
          <div id="cost-hosting-detail" style="font-size:9px;color:var(--muted);margin-top:4px">$7/mo Always-on VM</div>
        </div>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 16px;background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:var(--radius-sm)">
        <span style="font-size:12px;color:var(--muted);font-weight:500">Total per episode</span>
        <span id="cost-total" style="font-size:15px;font-weight:700;color:var(--text)">$0.00</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;padding:10px 16px;background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:var(--radius-sm)">
        <span style="font-size:12px;color:var(--muted);font-weight:500">Monthly (30 episodes + hosting)</span>
        <span id="cost-monthly" style="font-size:15px;font-weight:700;color:var(--text)">$0.00</span>
      </div>
    </div>
  </div>

  <div class="card" style="margin-bottom:24px">
    <div class="collapse-toggle open" onclick="togglePromptEditor(this)" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <div class="card-title" style="margin:0"><span class="arrow">&#9654;</span>Prompt Editor</div>
      <span id="prompt-status" style="font-size:11px;color:var(--muted);font-weight:500"></span>
    </div>
    <div id="prompt-editor-body">
      <div style="font-size:12px;color:var(--muted);margin-bottom:16px;line-height:1.6">
        Edit the prompt sections below. Changes are used when generating new episodes.
      </div>
      <div id="prompt-sections-container">Loading prompt sections...</div>
      <div class="prompt-actions" style="margin-top:16px;border-top:1px solid var(--border);padding-top:16px">
        <button class="small-btn" onclick="resetAllPromptSections()" style="background:rgba(248,113,113,.1);border-color:rgba(248,113,113,.2);color:var(--red)">Reset All to Defaults</button>
        <button class="small-btn" onclick="savePromptSections()" style="background:rgba(52,211,153,.1);border-color:rgba(52,211,153,.2);color:var(--green)">Save All Changes</button>
      </div>
    </div>
  </div>

  </div>

  <div class="tab-panel" id="panel-history" role="tabpanel" aria-labelledby="tab-btn-history" aria-hidden="true">

  <div class="card" style="margin-bottom:24px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <div class="card-title" style="margin:0">Episode History</div>
      <button class="small-btn" onclick="loadEpisodes()">Refresh</button>
    </div>
    <div id="ep-container">
      <div class="empty">Loading episodes...</div>
    </div>
  </div>

  <div class="card" style="margin-bottom:24px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <div class="card-title" style="margin:0">Generated Files</div>
      <button class="small-btn" onclick="loadFiles()">Refresh</button>
    </div>
    <div id="files-container">
      <div class="empty">Loading files...</div>
    </div>
  </div>

  </div>

  <div class="footer">Mind the Gap v1.0</div>

</div>

<div class="modal-bg" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title" id="modal-title">Transcript</div>
      <button class="modal-close" onclick="closeModal()">&#10005;</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
    <div id="modal-approval" style="display:none;padding-top:16px;border-top:1px solid var(--border);margin-top:16px;display:none">
      <div style="display:flex;gap:12px;justify-content:flex-end">
        <button class="btn" style="width:auto;padding:10px 20px" onclick="approveScript(false)">
          <span class="btn-icon">🎙</span> Approve &amp; Generate Audio
        </button>
        <button class="btn primary" style="width:auto;padding:10px 20px" onclick="approveScript(true)">
          <span class="btn-icon">🚀</span> Approve &amp; Publish
        </button>
      </div>
    </div>
  </div>
</div>

<div class="modal-bg" id="compare-modal" onclick="if(event.target===this)closeCompare()">
  <div class="modal" style="max-width:1100px;width:95%">
    <div class="modal-header">
      <div class="modal-title">Compare Script Models</div>
      <button class="modal-close" onclick="closeCompare()">&#10005;</button>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;padding:16px 0">
      <div>
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
          <select id="cmp-model-a" class="setting-select" style="flex:1"></select>
          <button class="small-btn" id="cmp-btn-a" onclick="runPreview('a')" style="white-space:nowrap">Generate</button>
        </div>
        <div id="cmp-stats-a" style="font-size:11px;color:var(--muted);margin-bottom:8px;min-height:18px"></div>
        <div id="cmp-output-a" class="console" style="height:500px;font-size:12px;overflow:auto;white-space:pre-wrap">
          <div class="log-line info">Select a model and click Generate</div>
        </div>
      </div>
      <div>
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
          <select id="cmp-model-b" class="setting-select" style="flex:1"></select>
          <button class="small-btn" id="cmp-btn-b" onclick="runPreview('b')" style="white-space:nowrap">Generate</button>
        </div>
        <div id="cmp-stats-b" style="font-size:11px;color:var(--muted);margin-bottom:8px;min-height:18px"></div>
        <div id="cmp-output-b" class="console" style="height:500px;font-size:12px;overflow:auto;white-space:pre-wrap">
          <div class="log-line info">Select a model and click Generate</div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="modal-bg" id="revoice-modal" onclick="if(event.target===this)closeRevoice()">
  <div class="modal" style="max-width:460px">
    <div class="modal-header">
      <div class="modal-title">🎙 Revoice Episode</div>
      <button class="modal-close" onclick="closeRevoice()">&#10005;</button>
    </div>
    <div class="modal-body" style="overflow:visible">
      <p style="color:var(--muted);font-size:13px;margin:0 0 16px">Re-generate audio for <strong id="revoice-date-label" style="color:var(--text)"></strong> using the voices currently selected in Configure.</p>
      <div style="background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:20px">
        <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:8px">
          <span style="color:var(--muted)">TTS Provider</span>
          <span id="revoice-tts-provider" style="color:var(--accent);font-weight:500"></span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:8px">
          <span style="color:var(--muted)">Alex (host)</span>
          <span id="revoice-voice-alex" style="color:#58a6ff;font-weight:500"></span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:13px">
          <span style="color:var(--muted)">Maya (host)</span>
          <span id="revoice-voice-maya" style="color:#bc8cff;font-weight:500"></span>
        </div>
      </div>
      <p style="font-size:12px;color:var(--muted);margin:0 0 20px">This keeps the existing script — only the audio synthesis changes. The old audio file will be replaced. Change voices in the Configure tab first if needed.</p>
      <div style="display:flex;gap:10px">
        <button class="btn" style="flex:1" onclick="startRevoice(false)">
          <span class="btn-icon">🎵</span>
          <div><div style="font-weight:600">Revoice only</div><div style="font-size:11px;opacity:.55;margin-top:2px">Generate new audio, no publish</div></div>
        </button>
        <button class="btn primary" style="flex:1" onclick="startRevoice(true)">
          <span class="btn-icon">📡</span>
          <div><div style="font-weight:600">Revoice &amp; Publish</div><div style="font-size:11px;opacity:.55;margin-top:2px">Generate audio and push to Transistor</div></div>
        </button>
      </div>
    </div>
  </div>
</div>

<script>
// ── Tab switching ─────────────────────────────────────────────────────────────
const _tabIds = ['run', 'configure', 'history'];
function switchTab(tab) {
  if (!_tabIds.includes(tab)) return;
  _tabIds.forEach(id => {
    const btn = document.getElementById('tab-btn-' + id);
    const panel = document.getElementById('panel-' + id);
    const isActive = id === tab;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive);
    btn.setAttribute('tabindex', isActive ? '0' : '-1');
    panel.classList.toggle('active', isActive);
    panel.setAttribute('aria-hidden', !isActive);
  });
}
document.querySelector('[role="tablist"]')?.addEventListener('keydown', e => {
  const keys = { ArrowRight: 1, ArrowLeft: -1, Home: -99, End: 99 };
  const dir = keys[e.key];
  if (dir == null) return;
  e.preventDefault();
  const cur = _tabIds.indexOf(document.querySelector('.tab-btn.active')?.id.replace('tab-btn-', ''));
  let next;
  if (e.key === 'Home') next = 0;
  else if (e.key === 'End') next = _tabIds.length - 1;
  else next = (cur + dir + _tabIds.length) % _tabIds.length;
  switchTab(_tabIds[next]);
  document.getElementById('tab-btn-' + _tabIds[next]).focus();
});

// ── State ──────────────────────────────────────────────────────────────────────
let autoscroll = true;
let es = null;
let pollTimer = null;
let _lastStatus = null;
let _approvalDate = null;
let _modelOptions = [];

// ── Init ───────────────────────────────────────────────────────────────────────
let settingsTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  loadStatus();
  loadEpisodes();
  loadFiles();
  loadSettings();
  loadPromptSections();
  connectSSE();
  checkSocialStatus();
  pollTimer = setInterval(loadStatus, 3000);
});

async function checkSocialStatus() {
  try {
    const r = await fetch('/api/social-status').then(r => r.json());
    const el = document.getElementById('social-status');
    if (r.configured) {
      el.textContent = 'Active (web search)';
      el.style.color = 'var(--green)';
    } else {
      el.textContent = 'Inactive';
      el.style.color = 'var(--yellow)';
    }
  } catch(e) {}
}

// ── Status polling ─────────────────────────────────────────────────────────────
async function loadStatus() {
  const r = await fetch('/api/status').then(r => r.json());
  _lastStatus = r;
  const badge  = document.getElementById('status-badge');
  const dot    = document.getElementById('status-dot');
  const text   = document.getElementById('status-text');
  const header = document.getElementById('header-status');
  const info   = document.getElementById('last-run-info');

  const btns = ['btn-full','btn-script','btn-nopub'];

  const stopBtn = document.getElementById('btn-stop');

  if (r.running) {
    badge.className = 'status-badge running';
    dot.className = 'dot pulse';
    dot.style.background = '';
    text.textContent = `Running — ${r.mode}`;
    header.textContent = `Running [${r.mode}] since ${fmt(r.started_at)}`;
    btns.forEach(id => document.getElementById(id).disabled = true);
    stopBtn.style.display = 'flex';
  } else {
    stopBtn.style.display = 'none';
    if (r.exit_code === null) {
      badge.className = 'status-badge idle';
      dot.className = 'dot';
      dot.style.background = '';
      text.textContent = 'Idle';
      header.textContent = 'Ready';
    } else if (r.exit_code === 0) {
      badge.className = 'status-badge idle';
      dot.className = 'dot';
      dot.style.background = '';
      text.textContent = 'Last run: success';
      header.textContent = `Last run succeeded at ${fmt(r.finished_at)}`;
    } else {
      badge.className = 'status-badge failed';
      dot.className = 'dot';
      dot.style.background = '';
      text.textContent = `Last run: failed (exit ${r.exit_code})`;
      header.textContent = `Last run failed at ${fmt(r.finished_at)}`;
    }
    btns.forEach(id => document.getElementById(id).disabled = false);

    if (r.started_at) {
      const dur = r.finished_at
        ? ((new Date(r.finished_at) - new Date(r.started_at)) / 1000 / 60).toFixed(1) + ' min'
        : '—';
      info.innerHTML = `<div style="font-size:12px;color:var(--muted);line-height:1.8">
        Started: ${fmt(r.started_at)} &nbsp;·&nbsp; Finished: ${fmt(r.finished_at)} &nbsp;·&nbsp; Mode: ${r.mode} &nbsp;·&nbsp; Duration: ${dur}
      </div>`;
    }

    const reviewBanner = document.getElementById('review-banner');
    if (r.awaiting_approval && r.approval_script_date) {
      badge.className = 'status-badge running';
      dot.className = 'dot';
      dot.style.background = 'var(--yellow)';
      text.textContent = 'Awaiting review';
      header.textContent = `Script ready — review & approve (${r.approval_script_date})`;
      reviewBanner.style.display = 'block';
    } else {
      reviewBanner.style.display = 'none';
    }
  }
}

function openPendingReview() {
  if (_lastStatus && _lastStatus.awaiting_approval && _lastStatus.approval_script_date) {
    showTranscript(_lastStatus.approval_script_date, 'Review Script — ' + _lastStatus.approval_script_date);
  }
}

// ── Run job ────────────────────────────────────────────────────────────────────
async function runJob(mode) {
  document.getElementById('console').innerHTML = '';
  const r = await fetch(`/api/run/${mode}`, {method:'POST'});
  if (!r.ok) {
    const err = await r.json();
    appendLog('error', `Error: ${err.error}`);
    return;
  }
  appendLog('start', `Started [${mode}] run…`);
  loadStatus();
  connectSSE();
}

async function stopJob() {
  const r = await fetch('/api/stop', {method:'POST'});
  if (!r.ok) {
    const err = await r.json();
    appendLog('error', `Error: ${err.error}`);
    return;
  }
  appendLog('warn', 'Job stopped by user.');
  loadStatus();
}

// ── SSE log stream ─────────────────────────────────────────────────────────────
function connectSSE() {
  if (es) es.close();
  es = new EventSource('/api/stream');
  es.onmessage = (ev) => {
    if (ev.data === '__DONE__') {
      loadEpisodes();
      loadFiles();
      loadStatus().then(() => {
        const status = _lastStatus;
        if (status && status.awaiting_approval && status.approval_script_date) {
          showTranscript(status.approval_script_date, 'Review Script — ' + status.approval_script_date);
        }
      });
      return;
    }
    const line = JSON.parse(ev.data);
    appendLog(classifyLine(line), line);
  };
  es.onerror = () => { /* auto-reconnects */ };
}

function classifyLine(line) {
  if (/✓ SUCCESS/.test(line)) return 'ok';
  if (/✗ FAILED|ERROR/.test(line)) return 'fail';
  if (/▶ Start/.test(line)) return 'start';
  if (/=== STEP/.test(line)) return 'step';
  if (/WARNING/.test(line)) return 'warn';
  if (/INFO/.test(line)) return 'info';
  return 'info';
}

function appendLog(cls, text) {
  const con = document.getElementById('console');
  const el = document.createElement('div');
  el.className = `log-line ${cls}`;
  el.textContent = text.replace(/\n$/, '');
  con.appendChild(el);
  if (autoscroll) con.scrollTop = con.scrollHeight;
}

function clearConsole() {
  document.getElementById('console').innerHTML = '';
}

function toggleAutoscroll() {
  autoscroll = !autoscroll;
  document.getElementById('btn-autoscroll').textContent =
    `Auto-scroll: ${autoscroll ? 'ON' : 'OFF'}`;
}

// ── Episodes ───────────────────────────────────────────────────────────────────
async function loadEpisodes() {
  const eps = await fetch('/api/episodes').then(r => r.json());
  const con = document.getElementById('ep-container');

  // Update stats
  const published = eps.filter(e => e.status === 'published' || e.share_url);
  document.getElementById('stat-total').textContent = published.length;
  if (eps.length > 0) {
    const lastTs = eps[0].published_at || eps[0].generated_at;
    document.getElementById('stat-last').textContent = lastTs ? fmt(lastTs) : (eps[0].date || '—');
  }
  const withDur = eps.filter(e => e.duration);
  if (withDur.length > 0) {
    const avg = withDur.reduce((s,e) => s + e.duration, 0) / withDur.length;
    document.getElementById('stat-runtime').textContent = fmtDur(avg);
  }

  if (eps.length === 0) {
    con.innerHTML = '<div class="empty">No episodes yet. Run the pipeline to generate your first episode.</div>';
    return;
  }

  const rows = eps.map(ep => {
    const statusBadge = ep.status === 'published'
      ? '<span class="badge-pub">● published</span>'
      : ep.has_audio
        ? '<span class="badge-draft">● local only</span>'
        : '<span style="color:var(--muted);font-size:11px">● script only</span>';

    const listenBtn = ep.share_url
      ? `<a class="pill listen" href="${ep.share_url}" target="_blank">▶ Listen</a>`
      : '';
    const scriptBtn = ep.has_script
      ? `<button class="pill script" onclick="showFile('${ep.date}_script.json','Script — ${ep.date}')">🧾 Script</button>`
      : '';
    const transcriptBtn = ep.has_transcript
      ? `<button class="pill transcript" onclick="showTranscript('${ep.date}','${ep.title?.replace(/'/g,"\\'")}')">📄 Transcript</button>`
      : '';
    const memoryBtn = `<button class="pill memory" id="mem-btn-${ep.date}" onclick="toggleMemory('${ep.date}')">🧠 Memory</button>`;
    const revoiceBtn = ep.has_script
      ? `<button class="pill" style="background:rgba(167,139,250,.1);border-color:rgba(167,139,250,.3);color:var(--accent)" onclick="openRevoice('${ep.date}')">🎙 Revoice</button>`
      : '';

    const dur = ep.duration ? fmtDur(ep.duration) : ep.size_mb ? `~${ep.size_mb}MB` : '—';
    const title = ep.title || ep.date;
    const ts = ep.published_at ? fmt(ep.published_at) : ep.generated_at ? fmt(ep.generated_at) : '—';
    const tsLabel = ep.published_at ? 'Published' : ep.generated_at ? 'Generated' : '';

    return `<tr class="ep-row">
      <td class="ep-date">${ep.date}</td>
      <td class="ep-title">${escHtml(title)}<br><span style="font-size:11px;color:var(--muted)">${statusBadge}</span></td>
      <td class="ep-dur">${dur}</td>
      <td class="ep-ts">${tsLabel ? `<span style="font-size:10px;color:var(--muted);display:block">${tsLabel}</span>${ts}` : '—'}</td>
      <td><div class="ep-actions">${listenBtn}${scriptBtn}${transcriptBtn}${revoiceBtn}${memoryBtn}</div></td>
    </tr>
    <tr class="mem-row"><td colspan="5" style="padding:0;border:none"><div class="memory-panel" id="mem-panel-${ep.date}"></div></td></tr>`;
  }).join('');

  con.innerHTML = `<table class="ep-table">
    <thead><tr>
      <th>Date</th><th>Title</th><th>Duration</th><th>Timestamp</th><th></th>
    </tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

// ── Story memory per episode ──────────────────────────────────────────────────
const _memoryCache = {};
async function toggleMemory(date) {
  const panel = document.getElementById('mem-panel-' + date);
  const btn = document.getElementById('mem-btn-' + date);
  if (panel.classList.contains('open')) {
    panel.classList.remove('open');
    btn.classList.remove('active');
    return;
  }
  btn.classList.add('active');
  panel.classList.add('open');
  if (_memoryCache[date]) {
    panel.innerHTML = renderMemoryStories(_memoryCache[date]);
    return;
  }
  panel.innerHTML = '<div class="memory-empty">Loading stories...</div>';
  try {
    const r = await fetch('/api/story-memory/' + date).then(r => r.json());
    _memoryCache[date] = r.stories || [];
    panel.innerHTML = renderMemoryStories(_memoryCache[date]);
  } catch(e) {
    panel.innerHTML = '<div class="memory-empty">Failed to load stories</div>';
  }
}

function renderMemoryStories(stories) {
  if (!stories || stories.length === 0) {
    return '<div class="memory-empty">No stories tracked for this episode</div>';
  }
  const validCats = {
    toronto_canada: 'Toronto/Canada',
    global_macro: 'Global Macro',
    ai_tech: 'AI/Tech',
    behavioural_spirituality: 'Behavioural',
    general: 'General'
  };
  return stories.map(s => {
    const rawCat = s.topic_category || 'general';
    const cat = validCats[rawCat] ? rawCat : 'general';
    const catLabel = validCats[cat];
    const entities = (s.key_entities || []).map(e => `<span class="memory-entity">${escHtml(e)}</span>`).join('');
    const contBadge = s.is_continuation ? '<span class="memory-continuation">continuation</span>' : '';
    return `<div class="memory-story">
      <div class="memory-story-header">
        <span class="memory-cat ${cat}">${catLabel}</span>
        <span class="memory-headline">${escHtml(s.headline || '')}</span>
        ${contBadge}
      </div>
      <div class="memory-summary">${escHtml(s.summary || '')}</div>
      ${entities ? `<div class="memory-entities">${entities}</div>` : ''}
    </div>`;
  }).join('');
}

// ── Transcript modal ───────────────────────────────────────────────────────────
async function showTranscript(date, title) {
  _approvalDate = date;
  const r = await fetch(`/api/transcript/${date}`);
  if (!r.ok) return;
  const data = await r.json();
  document.getElementById('modal-title').textContent = title || 'Transcript';
  let safe = escHtml(data.transcript);
  let formatted = safe.replace(
    /^(ALEX|MAYA):/gm,
    (_, name) => `<strong style="color:${name==='ALEX'?'#58a6ff':'#bc8cff'}">${name}:</strong>`
  );
  formatted = formatted.replace(
    /^\[Sound: (.+?)\]$/gm,
    (_, desc) => `<em style="color:#7d8590">[Sound: ${desc}]</em>`
  );
  document.getElementById('modal-body').innerHTML = formatted;

  const approvalDiv = document.getElementById('modal-approval');
  if (_lastStatus && _lastStatus.awaiting_approval && _lastStatus.approval_script_date === date) {
    approvalDiv.style.display = 'block';
  } else {
    approvalDiv.style.display = 'none';
  }

  document.getElementById('modal').classList.add('open');
}

async function approveScript(publish) {
  closeModal();
  if (!_approvalDate) return;
  document.getElementById('console').innerHTML = '';
  const r = await fetch('/api/approve-script', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({date: _approvalDate, publish: publish}),
  });
  if (!r.ok) {
    const err = await r.json();
    appendLog('error', 'Error: ' + err.error);
    return;
  }
  const mode = publish ? 'full (from script)' : 'audio only (from script)';
  appendLog('start', '▶ Approved — starting ' + mode + '…');
  loadStatus();
  connectSSE();
}

function closeModal() {
  document.getElementById('modal').classList.remove('open');
  document.getElementById('modal-approval').style.display = 'none';
}

// ── Revoice modal ────────────────────────────────────────────────────────────
let _revoiceDate = null;

async function openRevoice(date) {
  _revoiceDate = date;
  document.getElementById('revoice-date-label').textContent = date;
  // Load current voice names from settings
  try {
    const s = await fetch('/api/settings').then(r => r.json());
    const opts = s._voice_options || {};
    const allVoices = [...(opts.male || []), ...(opts.female || [])];
    const nameMap = {};
    allVoices.forEach(v => { nameMap[v.id] = v.name; });
    const provider = s.tts_provider || 'elevenlabs';
    document.getElementById('revoice-tts-provider').textContent = provider === 'openai' ? 'OpenAI gpt-4o-mini-tts (Onyx / Nova)' : 'ElevenLabs (GenFM)';
    if (provider === 'openai') {
      document.getElementById('revoice-voice-alex').textContent = 'Onyx';
      document.getElementById('revoice-voice-maya').textContent = 'Nova';
    } else {
      document.getElementById('revoice-voice-alex').textContent = nameMap[s.voice_alex] || s.voice_alex || '—';
      document.getElementById('revoice-voice-maya').textContent = nameMap[s.voice_maya] || s.voice_maya || '—';
    }
  } catch(e) {
    document.getElementById('revoice-tts-provider').textContent = '—';
    document.getElementById('revoice-voice-alex').textContent = '—';
    document.getElementById('revoice-voice-maya').textContent = '—';
  }
  document.getElementById('revoice-modal').classList.add('open');
}

function closeRevoice() {
  document.getElementById('revoice-modal').classList.remove('open');
}

async function startRevoice(publish) {
  if (!_revoiceDate) return;
  closeRevoice();
  switchTab('run');
  document.getElementById('console').innerHTML = '';
  const r = await fetch('/api/revoice', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ date: _revoiceDate, publish })
  });
  const data = await r.json();
  if (!r.ok) {
    appendLog('error', 'Revoice failed: ' + (data.error || r.status));
    return;
  }
  appendLog('start', `▶ Revoice started for ${data.date} using ${data.voice_alex} & ${data.voice_maya}${publish ? ' — will publish when done' : ''}`);
  loadStatus();
  connectSSE();
}

// ── Files browser ───────────────────────────────────────────────────────────
async function loadFiles() {
  const files = await fetch('/api/files').then(r => r.json());
  const con = document.getElementById('files-container');

  if (files.length === 0) {
    con.innerHTML = '<div class="empty">No output files yet. Run the pipeline to generate files.</div>';
    return;
  }

  const icons = { script: '🧾', transcript: '📄', description: '📝', audio: '🎵', other: '📎' };
  const grouped = {};
  files.forEach(f => {
    const date = f.name.replace(/_.+$/, '') || 'other';
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(f);
  });

  let html = '';
  for (const [date, group] of Object.entries(grouped)) {
    const newest = group.reduce((a,b) => (a.modified > b.modified ? a : b));
    const ts = newest.modified ? fmt(newest.modified) : '';
    html += `<div class="file-group-title">${date}<span style="font-size:11px;color:var(--muted);margin-left:10px;font-weight:400">${ts}</span></div>`;
    group.forEach(f => {
      const icon = icons[f.type] || icons.other;
      const size = f.size > 1e6 ? (f.size / 1e6).toFixed(1) + ' MB' : (f.size / 1e3).toFixed(1) + ' KB';
      const fileTs = f.modified ? fmt(f.modified) : '';
      const viewable = f.type !== 'audio';
      const viewBtn = viewable
        ? `<button class="pill transcript" onclick="showFile('${f.name}','${f.name}')">View</button>`
        : `<a class="pill listen" href="/api/file/${f.name}" download>⬇ Download</a>`;
      html += `<div class="file-row">
        <div class="file-name"><span class="file-icon">${icon}</span><span>${f.name}</span></div>
        <div class="file-meta"><span style="color:var(--muted);font-size:11px;margin-right:8px">${fileTs}</span>${size}</div>
        <div class="file-actions">${viewBtn}</div>
      </div>`;
    });
  }
  con.innerHTML = html;
}

async function showFile(filename, title) {
  const r = await fetch(`/api/file/${filename}`);
  if (!r.ok) return;
  const data = await r.json();
  let content = data.content || '';
  document.getElementById('modal-title').textContent = title || filename;
  if (filename.endsWith('.json')) {
    try { content = JSON.stringify(JSON.parse(content), null, 2); } catch(e) {}
  }
  if (filename.endsWith('_transcript.txt')) {
    content = escHtml(content);
    content = content.replace(
      /^(ALEX|MAYA):/gm,
      (_, name) => `<strong style="color:${name==='ALEX'?'#58a6ff':'#bc8cff'}">${name}:</strong>`
    );
    content = content.replace(
      /^\[Sound: (.+?)\]$/gm,
      (_, desc) => `<em style="color:#7d8590">[Sound: ${desc}]</em>`
    );
    document.getElementById('modal-body').innerHTML = content;
  } else {
    document.getElementById('modal-body').textContent = content;
  }
  document.getElementById('modal').classList.add('open');
}

// ── Settings ──────────────────────────────────────────────────────────────────
const SETTING_KEYS = ['story_count','behavioral_concepts','spirituality_concepts',
  'geo_toronto_pct','geo_canada_pct','geo_ai_tech_pct','geo_world_pct','audio_speed'];
const SELECT_SETTING_KEYS = ['tts_provider'];
const TEXTAREA_SETTING_KEYS = ['voice_direction_alex', 'voice_direction_maya'];
const GEO_KEYS = ['geo_toronto_pct','geo_canada_pct','geo_ai_tech_pct','geo_world_pct'];

async function loadSettings() {
  try {
    const data = await fetch('/api/settings').then(r => r.json());

    SETTING_KEYS.forEach(key => {
      const el = document.getElementById('s-' + key);
      if (el) el.value = data[key] ?? el.value;
      const valEl = document.getElementById('val-' + key);
      if (valEl) {
        valEl.textContent = (GEO_KEYS.includes(key) || key === 'audio_speed') ? data[key] + '%' : data[key];
      }
    });

    updateGeoBar();

    const opts = data._voice_options || {};
    const alexSel = document.getElementById('s-voice_alex');
    const mayaSel = document.getElementById('s-voice_maya');

    if (opts.male) {
      alexSel.innerHTML = opts.male.map(v =>
        `<option value="${v.id}" ${v.id === data.voice_alex ? 'selected' : ''}>${v.name}</option>`
      ).join('');
    }
    if (opts.female) {
      mayaSel.innerHTML = opts.female.map(v =>
        `<option value="${v.id}" ${v.id === data.voice_maya ? 'selected' : ''}>${v.name}</option>`
      ).join('');
    }

    SELECT_SETTING_KEYS.forEach(key => {
      const el = document.getElementById('s-' + key);
      if (el) el.value = data[key] ?? el.value;
    });
    TEXTAREA_SETTING_KEYS.forEach(key => {
      const el = document.getElementById('s-' + key);
      if (el) el.value = data[key] ?? '';
    });

    window._openaiKeySet = data._openai_key_set !== false;
    updateTtsProviderUI();

    renderCustomVoices(data.custom_voices || []);

    _modelOptions = data._model_options || [];
    const modelSel = document.getElementById('s-script_model');
    const fallbackSel = document.getElementById('s-fallback_model');
    modelSel.innerHTML = _modelOptions.map(m =>
      `<option value="${m.id}" ${m.id === data.script_model ? 'selected' : ''}>${m.name}</option>`
    ).join('');
    fallbackSel.innerHTML = _modelOptions.map(m =>
      `<option value="${m.id}" ${m.id === data.fallback_model ? 'selected' : ''}>${m.name}</option>`
    ).join('');

    document.querySelectorAll('.setting-slider').forEach(el => {
      el.addEventListener('input', onSettingChange);
    });
    alexSel.addEventListener('change', onSettingChange);
    mayaSel.addEventListener('change', onSettingChange);
    document.querySelectorAll('.setting-textarea').forEach(el => {
      el.addEventListener('input', onSettingChange);
    });

    updateCostEstimate();
  } catch(e) {
    console.error('Failed to load settings', e);
  }
}

function renderCustomVoices(voices) {
  const el = document.getElementById('custom-voices-list');
  if (!voices || voices.length === 0) { el.innerHTML = ''; return; }
  el.innerHTML = '<div style="font-size:11px;color:var(--muted);margin-bottom:6px;font-weight:500">Custom Voices</div>' +
    voices.map(v => `<div style="display:flex;align-items:center;gap:8px;padding:4px 0">
      <span style="font-size:12px;color:var(--text)">${escHtml(v.name)}</span>
      <span style="font-size:10px;color:var(--muted);font-family:monospace">${v.id.slice(0,12)}…</span>
      <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:${v.gender==='male'?'rgba(88,166,255,.12)':'rgba(188,140,255,.12)'};color:${v.gender==='male'?'#58a6ff':'#bc8cff'}">${v.gender==='male'?'Alex':'Maya'}</span>
      <button onclick="removeCustomVoice('${v.id}')" style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:14px;padding:0 4px" title="Remove">&times;</button>
    </div>`).join('');
}

async function addCustomVoice() {
  const id = document.getElementById('cv-id').value.trim();
  const name = document.getElementById('cv-name').value.trim();
  const gender = document.getElementById('cv-gender').value;
  const status = document.getElementById('cv-status');
  if (!id) { status.textContent = 'Voice ID is required'; status.style.color = '#f87171'; return; }
  status.textContent = 'Adding…'; status.style.color = 'var(--muted)';
  const r = await fetch('/api/custom-voice', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ id, name, gender })
  });
  const data = await r.json();
  if (!r.ok) { status.textContent = data.error || 'Failed'; status.style.color = '#f87171'; return; }
  status.textContent = 'Added!'; status.style.color = '#34d399';
  document.getElementById('cv-id').value = '';
  document.getElementById('cv-name').value = '';
  loadSettings();
  setTimeout(() => { status.textContent = ''; }, 2000);
}

async function removeCustomVoice(id) {
  const r = await fetch('/api/custom-voice/' + encodeURIComponent(id), { method: 'DELETE' });
  if (r.ok) loadSettings();
}

function updateTtsProviderUI() {
  const provider = document.getElementById('s-tts_provider')?.value || 'elevenlabs';
  const elConfig = document.getElementById('elevenlabs-voice-config');
  const oaiConfig = document.getElementById('openai-voice-config');
  const hint = document.getElementById('tts-provider-hint');
  if (provider === 'openai') {
    elConfig.style.display = 'none';
    oaiConfig.style.display = 'block';
    if (window._openaiKeySet === false) {
      hint.innerHTML = '<span style="color:#f87171">⚠ OPENAI_API_KEY is not configured. Add it in Secrets before generating audio.</span>';
    } else {
      hint.textContent = 'Uses gpt-4o-mini-tts with voice direction instructions for natural podcast delivery.';
    }
  } else {
    elConfig.style.display = 'block';
    oaiConfig.style.display = 'none';
    hint.textContent = '';
  }
  updateCostEstimate();
}

function onTtsProviderChange() {
  updateTtsProviderUI();
  const statusEl = document.getElementById('settings-status');
  statusEl.textContent = 'Saving...';
  statusEl.className = 'saving';
  clearTimeout(settingsTimer);
  settingsTimer = setTimeout(saveSettings, 600);
}

function onSettingChange(ev) {
  const el = ev.target;
  const key = el.id.replace('s-', '');
  const val = el.type === 'range' ? parseInt(el.value) : el.value;

  const valEl = document.getElementById('val-' + key);
  if (valEl) {
    valEl.textContent = (GEO_KEYS.includes(key) || key === 'audio_speed') ? val + '%' : val;
  }
  if (GEO_KEYS.includes(key)) updateGeoBar();
  updateCostEstimate();

  const statusEl = document.getElementById('settings-status');
  statusEl.textContent = 'Saving...';
  statusEl.className = 'saving';
  clearTimeout(settingsTimer);
  settingsTimer = setTimeout(saveSettings, 600);
}

const MODEL_PRICING = {
  'claude-opus':     {inPer1M: 15, outPer1M: 75, thinkPer1M: 15, label: 'Claude Opus 4.6'},
  'gemini-3.1-pro':  {inPer1M: 2, outPer1M: 12, thinkPer1M: 0, label: 'Gemini 3.1 Pro'},
  'gpt-5.4':         {inPer1M: 2.5, outPer1M: 15, thinkPer1M: 0, label: 'GPT-5.4'},
  'deepseek-v3.2':   {inPer1M: 0.25, outPer1M: 0.40, thinkPer1M: 0, label: 'DeepSeek V3.2'},
};

function updateCostEstimate() {
  const n = parseInt(document.getElementById('s-story_count').value) || 1;
  const targetWords = Math.min(1550 + (n - 1) * 220, 3100);
  const estMinutes = Math.round(targetWords / 180);
  const estChars = Math.round(targetWords * 6.1);

  const modelKey = document.getElementById('s-script_model')?.value || 'claude-opus';
  const pricing = MODEL_PRICING[modelKey] || MODEL_PRICING['claude-opus'];

  const inputTokens = 4000 + n * 500;
  const thinkingTokens = modelKey === 'claude-opus' ? (5000 + n * 800) : 0;
  const outputTokens = Math.round(targetWords * 1.35);
  const titleTokens = 200;
  const llmInput = (inputTokens + titleTokens) / 1e6 * pricing.inPer1M;
  const llmThinking = thinkingTokens / 1e6 * pricing.thinkPer1M;
  const llmOutput = (outputTokens + 50) / 1e6 * pricing.outPer1M;
  const llmCost = llmInput + llmThinking + llmOutput;

  const ttsProvider = document.getElementById('s-tts_provider')?.value || 'elevenlabs';
  const dialogueChars = estChars;
  const sfxCredits = n * 400;
  let ttsCost, ttsDetail, ttsLabel;
  if (ttsProvider === 'openai') {
    ttsCost = dialogueChars / 1e6 * 15;
    const sfxCost = sfxCredits * 0.00022;
    ttsCost += sfxCost;
    ttsDetail = '~' + (dialogueChars / 1000).toFixed(1) + 'K chars @ $15/1M + SFX $' + sfxCost.toFixed(2);
    ttsLabel = 'OpenAI TTS + SFX';
  } else {
    const totalCredits = dialogueChars + sfxCredits;
    ttsCost = totalCredits * 0.00022;
    ttsDetail = '~' + (totalCredits / 1000).toFixed(1) + 'K credits (' + dialogueChars.toLocaleString() + ' chars)';
    ttsLabel = 'ElevenLabs';
  }

  const hostingPerEp = 7.0 / 30;

  const totalEpisode = llmCost + ttsCost + hostingPerEp;
  const monthly = totalEpisode * 30;

  document.getElementById('cost-llm-label').textContent = pricing.label;
  document.getElementById('cost-anthropic').textContent = '$' + llmCost.toFixed(2);
  let detail = '~' + ((inputTokens + titleTokens) / 1000).toFixed(1) + 'K in + ' +
    ((outputTokens + 50) / 1000).toFixed(1) + 'K out';
  if (thinkingTokens > 0) detail = '~' + ((inputTokens + titleTokens) / 1000).toFixed(1) + 'K in + ' +
    (thinkingTokens / 1000).toFixed(1) + 'K think + ' +
    ((outputTokens + 50) / 1000).toFixed(1) + 'K out';
  document.getElementById('cost-anthropic-detail').textContent = detail;

  document.getElementById('cost-elevenlabs-label').textContent = ttsLabel;
  document.getElementById('cost-elevenlabs').textContent = '$' + ttsCost.toFixed(2);
  document.getElementById('cost-elevenlabs-detail').textContent = ttsDetail;

  document.getElementById('cost-hosting').textContent = '$' + hostingPerEp.toFixed(2);
  document.getElementById('cost-hosting-detail').textContent = '$7/mo Always-on VM';

  document.getElementById('cost-total').textContent = '$' + totalEpisode.toFixed(2);
  document.getElementById('cost-monthly').textContent = '$' + monthly.toFixed(2) + '/mo';
}

function onModelChange() {
  updateCostEstimate();
  const statusEl = document.getElementById('settings-status');
  statusEl.textContent = 'Saving...';
  statusEl.className = 'saving';
  clearTimeout(settingsTimer);
  settingsTimer = setTimeout(saveSettings, 600);
}

async function saveSettings() {
  const body = {};
  SETTING_KEYS.forEach(key => {
    body[key] = parseInt(document.getElementById('s-' + key).value);
  });
  body.voice_alex = document.getElementById('s-voice_alex').value;
  body.voice_maya = document.getElementById('s-voice_maya').value;
  body.tts_provider = document.getElementById('s-tts_provider').value;
  body.script_model = document.getElementById('s-script_model').value;
  body.fallback_model = document.getElementById('s-fallback_model').value;
  TEXTAREA_SETTING_KEYS.forEach(key => {
    const el = document.getElementById('s-' + key);
    if (el) body[key] = el.value;
  });

  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    const statusEl = document.getElementById('settings-status');
    statusEl.textContent = 'Saved';
    statusEl.className = 'saved';
    setTimeout(() => {
      statusEl.textContent = '';
      statusEl.className = '';
    }, 2000);
  } catch(e) {
    const statusEl = document.getElementById('settings-status');
    statusEl.textContent = 'Save failed';
    statusEl.className = '';
  }
}

// ── Prompt Editor ─────────────────────────────────────────────────────────────
const PROMPT_LABELS = {
  show_identity: 'Show Identity',
  host_alex: 'Host: Alex',
  host_maya: 'Host: Maya',
  episode_structure: 'Episode Structure',
};
let _promptData = {};

function togglePromptEditor(el) {
  el.classList.toggle('open');
  const body = document.getElementById('prompt-editor-body');
  body.style.display = el.classList.contains('open') ? 'block' : 'none';
}

async function loadPromptSections() {
  try {
    const data = await fetch('/api/prompt-sections').then(r => r.json());
    _promptData = data;
    const con = document.getElementById('prompt-sections-container');
    let html = '';
    for (const [key, info] of Object.entries(data)) {
      const label = PROMPT_LABELS[key] || key;
      const badge = info.is_custom
        ? '<span class="prompt-section-badge custom">Customized</span>'
        : '<span class="prompt-section-badge default">Default</span>';
      html += `<div class="prompt-section">
        <div class="prompt-section-header">
          <span class="prompt-section-label">${label}</span>
          <div style="display:flex;gap:8px;align-items:center">
            ${badge}
            ${info.is_custom ? `<button class="small-btn" onclick="resetPromptSection('${key}')" style="font-size:10px;padding:2px 8px">Reset</button>` : ''}
          </div>
        </div>
        <textarea class="prompt-textarea" id="prompt-${key}" rows="8">${escHtml(info.value)}</textarea>
      </div>`;
    }
    con.innerHTML = html;
  } catch(e) {
    console.error('Failed to load prompt sections', e);
  }
}

async function savePromptSections() {
  const body = {};
  for (const key of Object.keys(_promptData)) {
    const el = document.getElementById('prompt-' + key);
    if (el) body[key] = el.value;
  }
  try {
    const statusEl = document.getElementById('prompt-status');
    statusEl.textContent = 'Saving...';
    const resp = await fetch('/api/prompt-sections', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    if (!resp.ok) throw new Error('Save failed');
    statusEl.textContent = 'Saved';
    statusEl.style.color = '#3fb950';
    setTimeout(() => { statusEl.textContent = ''; statusEl.style.color = ''; }, 2000);
    loadPromptSections();
  } catch(e) {
    const statusEl = document.getElementById('prompt-status');
    statusEl.textContent = 'Save failed';
    statusEl.style.color = '#da3633';
  }
}

async function resetPromptSection(section) {
  if (!confirm('Reset "' + (PROMPT_LABELS[section] || section) + '" to default?')) return;
  try {
    const resp = await fetch('/api/prompt-sections/reset', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({section}),
    });
    if (!resp.ok) throw new Error('Reset failed');
    loadPromptSections();
  } catch(e) {
    console.error('Reset failed', e);
  }
}

async function resetAllPromptSections() {
  if (!confirm('Reset ALL prompt sections to defaults? This will discard all your customizations.')) return;
  try {
    const resp = await fetch('/api/prompt-sections/reset', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({}),
    });
    if (!resp.ok) throw new Error('Reset all failed');
    loadPromptSections();
  } catch(e) {
    console.error('Reset all failed', e);
  }
}

function updateGeoBar() {
  const t = parseInt(document.getElementById('s-geo_toronto_pct').value) || 0;
  const c = parseInt(document.getElementById('s-geo_canada_pct').value) || 0;
  const a = parseInt(document.getElementById('s-geo_ai_tech_pct').value) || 0;
  const w = parseInt(document.getElementById('s-geo_world_pct').value) || 0;
  const total = t + c + a + w || 1;
  document.getElementById('gbar-toronto').style.width = (t/total*100) + '%';
  document.getElementById('gbar-canada').style.width = (c/total*100) + '%';
  document.getElementById('gbar-ai-tech').style.width = (a/total*100) + '%';
  document.getElementById('gbar-world').style.width = (w/total*100) + '%';
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function fmt(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    timeZone: 'America/New_York',
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true
  }) + ' EST';
}

function fmtDur(sec) {
  const m = Math.floor(sec / 60), s = Math.round(sec % 60);
  return `${m}:${String(s).padStart(2,'0')}`;
}

function escHtml(s) {
  return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function openCompare() {
  const selA = document.getElementById('cmp-model-a');
  const selB = document.getElementById('cmp-model-b');
  selA.innerHTML = _modelOptions.map((m,i) =>
    `<option value="${m.id}" ${i===0?'selected':''}>${m.name}</option>`
  ).join('');
  selB.innerHTML = _modelOptions.map((m,i) =>
    `<option value="${m.id}" ${i===1?'selected':''}>${m.name}</option>`
  ).join('');
  document.getElementById('compare-modal').classList.add('open');
}

function closeCompare() {
  document.getElementById('compare-modal').classList.remove('open');
}

async function runPreview(side) {
  const sel = document.getElementById('cmp-model-' + side);
  const btn = document.getElementById('cmp-btn-' + side);
  const stats = document.getElementById('cmp-stats-' + side);
  const output = document.getElementById('cmp-output-' + side);
  const model = sel.value;
  const modelName = sel.options[sel.selectedIndex].text;

  btn.disabled = true;
  btn.textContent = 'Generating...';
  stats.textContent = '';
  output.innerHTML = '<div class="log-line info">Fetching news and generating script with ' + escHtml(modelName) + '... This may take 1-3 minutes.</div>';

  try {
    const r = await fetch('/api/preview-script', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({model: model}),
    });
    const data = await r.json();
    if (data.error) {
      output.innerHTML = '<div class="log-line error">Error: ' + escHtml(data.error) + '</div>';
      stats.textContent = '';
    } else {
      stats.textContent = modelName + ' | ' + data.stats.word_count + ' words | ' +
        data.stats.dialogue_turns + ' turns | ' + data.stats.elapsed_seconds + 's';
      let html = escHtml(data.formatted);
      html = html.replace(/^(ALEX):/gm, '<strong style="color:#58a6ff">ALEX:</strong>');
      html = html.replace(/^(MAYA):/gm, '<strong style="color:#bc8cff">MAYA:</strong>');
      html = html.replace(/^\[Sound: (.+?)\]$/gm, '<em style="color:#7d8590">[Sound: $1]</em>');
      output.innerHTML = html;
    }
  } catch(e) {
    output.innerHTML = '<div class="log-line error">Request failed: ' + escHtml(e.message) + '</div>';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate';
  }
}
</script>
</body>
</html>"""
