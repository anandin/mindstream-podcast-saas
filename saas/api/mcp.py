"""
CastAPI MCP Server — JSON-RPC 2.0 endpoint.

Exposes Mind Stream podcast generation as MCP tools so any MCP-compatible
AI agent (Claude, Cursor, etc.) can generate, query, and manage episodes.

Endpoint:  POST /mcp
Auth:      X-API-Key: msk_<your-key>

Tools:
  - generate_episode     Start async episode generation
  - get_episode_status   Poll generation status + audio URL
  - list_voices          Available TTS voices
  - list_podcasts        Podcasts owned by the caller
  - create_podcast       Create a new podcast show
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from saas.api.main import get_db
from saas.auth.auth import hash_api_key, verify_api_key
from saas.db.models import User, Podcast, Episode, APIKey, SubscriptionTier

router = APIRouter()

# ── MCP protocol constants ────────────────────────────────────────────────────

MCP_VERSION = "2024-11-05"
SERVER_NAME = "castapi-mindstream"
SERVER_VERSION = "1.0.0"

# ── Available voices ──────────────────────────────────────────────────────────

VOICES = [
    {"id": "male-qn-qingse", "name": "Alex (English Male)", "language": "en", "provider": "minimax"},
    {"id": "female-shaonv",   "name": "Maya (English Female)", "language": "en", "provider": "minimax"},
    {"id": "male-qn-jingying","name": "Jordan (Energetic Male)", "language": "en", "provider": "minimax"},
    {"id": "female-yujie",    "name": "Sam (Professional Female)", "language": "en", "provider": "minimax"},
    {"id": "alloy",           "name": "Alloy (OpenAI Neutral)", "language": "en", "provider": "openai"},
    {"id": "nova",            "name": "Nova (OpenAI Female)", "language": "en", "provider": "openai"},
    {"id": "echo",            "name": "Echo (OpenAI Male)",   "language": "en", "provider": "openai"},
]


# ── Auth helper ───────────────────────────────────────────────────────────────

def _get_user_from_api_key(api_key_value: str, db: Session) -> User | None:
    """Resolve an API key string to the owning User, or None if invalid."""
    if not api_key_value or not api_key_value.startswith("msk_"):
        return None
    keys = db.query(APIKey).filter(APIKey.is_active == True).all()  # noqa: E712
    for key_record in keys:
        if verify_api_key(api_key_value, key_record.key_hash):
            # Bump usage
            key_record.total_calls = (key_record.total_calls or 0) + 1
            key_record.last_used_at = datetime.now(timezone.utc)
            db.commit()
            return key_record.user
    return None


# ── Tool handlers ─────────────────────────────────────────────────────────────

def _tool_list_voices(_params: dict, _user: User, _db: Session) -> dict:
    return {"voices": VOICES, "default_provider": "minimax"}


def _tool_list_podcasts(_params: dict, user: User, db: Session) -> dict:
    podcasts = db.query(Podcast).filter(
        Podcast.user_id == user.id, Podcast.is_active == True  # noqa: E712
    ).all()
    return {
        "podcasts": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "total_episodes": p.total_episodes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in podcasts
        ]
    }


def _tool_create_podcast(params: dict, user: User, db: Session) -> dict:
    title = params.get("title", "").strip()
    if not title:
        raise ValueError("title is required")

    podcast = Podcast(
        user_id=user.id,
        title=title,
        description=params.get("description", ""),
        host_1_name=params.get("host_1_name", "Alex"),
        host_2_name=params.get("host_2_name", "Maya"),
        tts_provider=params.get("tts_provider", user.default_tts_provider or "minimax"),
        language=params.get("language", "en"),
    )
    db.add(podcast)
    db.commit()
    db.refresh(podcast)
    return {"podcast_id": podcast.id, "title": podcast.title, "status": "created"}


def _tool_generate_episode(params: dict, user: User, db: Session) -> dict:
    podcast_id = params.get("podcast_id")
    if not podcast_id:
        raise ValueError("podcast_id is required")

    podcast = db.query(Podcast).filter(
        Podcast.id == podcast_id, Podcast.user_id == user.id
    ).first()
    if not podcast:
        raise ValueError(f"Podcast {podcast_id} not found or access denied")

    topic = params.get("topic", "").strip()
    if not topic:
        raise ValueError("topic is required")

    episode = Episode(
        podcast_id=podcast.id,
        date=datetime.now(timezone.utc),
        title=params.get("title") or f"Episode: {topic[:60]}",
        description=params.get("description", ""),
        status="queued",
    )
    db.add(episode)
    db.commit()
    db.refresh(episode)

    # Enqueue async generation job
    from saas.jobs.runner import enqueue_job
    enqueue_job(
        db=db,
        job_type="generate_episode",
        payload={
            "episode_id": episode.id,
            "podcast_id": podcast.id,
            "user_id": user.id,
            "topic": topic,
            "custom_notes": params.get("custom_notes", ""),
            "tts_provider": params.get("tts_provider", podcast.tts_provider),
            "host_1_voice": params.get("host_1_voice", podcast.host_1_voice_id),
            "host_2_voice": params.get("host_2_voice", podcast.host_2_voice_id),
        },
    )

    return {
        "episode_id": episode.id,
        "status": "queued",
        "message": "Episode generation started. Poll get_episode_status for updates.",
        "poll_interval_seconds": 10,
    }


def _tool_get_episode_status(params: dict, user: User, db: Session) -> dict:
    episode_id = params.get("episode_id")
    if not episode_id:
        raise ValueError("episode_id is required")

    episode = (
        db.query(Episode)
        .join(Podcast)
        .filter(Episode.id == episode_id, Podcast.user_id == user.id)
        .first()
    )
    if not episode:
        raise ValueError(f"Episode {episode_id} not found or access denied")

    result: dict[str, Any] = {
        "episode_id": episode.id,
        "title": episode.title,
        "status": episode.status,
        "created_at": episode.created_at.isoformat() if episode.created_at else None,
        "updated_at": episode.updated_at.isoformat() if episode.updated_at else None,
    }
    if episode.status == "ready":
        result["audio_url"] = episode.audio_url
        result["duration_seconds"] = episode.audio_duration_seconds
        result["publish_url"] = episode.publish_url
    if episode.status == "failed":
        result["error"] = episode.error_message
    return result


# ── Tool registry ─────────────────────────────────────────────────────────────

TOOLS = {
    "list_voices": {
        "handler": _tool_list_voices,
        "description": "List all available TTS voices for podcast generation.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "list_podcasts": {
        "handler": _tool_list_podcasts,
        "description": "List all podcast shows owned by the authenticated developer.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "create_podcast": {
        "handler": _tool_create_podcast,
        "description": "Create a new podcast show.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title":        {"type": "string", "description": "Show title"},
                "description":  {"type": "string", "description": "Show description"},
                "host_1_name":  {"type": "string", "description": "Name of host 1 (default: Alex)"},
                "host_2_name":  {"type": "string", "description": "Name of host 2 (default: Maya)"},
                "tts_provider": {"type": "string", "enum": ["minimax", "openai", "elevenlabs"]},
                "language":     {"type": "string", "description": "BCP-47 language code (default: en)"},
            },
            "required": ["title"],
        },
    },
    "generate_episode": {
        "handler": _tool_generate_episode,
        "description": (
            "Start async generation of a podcast episode. "
            "Returns an episode_id — poll get_episode_status until status is 'ready'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "podcast_id":   {"type": "integer", "description": "ID of the podcast show"},
                "topic":        {"type": "string",  "description": "Episode topic or content summary"},
                "title":        {"type": "string",  "description": "Optional episode title override"},
                "description":  {"type": "string",  "description": "Optional episode description"},
                "custom_notes": {"type": "string",  "description": "Additional instructions for the AI"},
                "tts_provider": {"type": "string",  "enum": ["minimax", "openai", "elevenlabs"]},
                "host_1_voice": {"type": "string",  "description": "Voice ID for host 1"},
                "host_2_voice": {"type": "string",  "description": "Voice ID for host 2"},
            },
            "required": ["podcast_id", "topic"],
        },
    },
    "get_episode_status": {
        "handler": _tool_get_episode_status,
        "description": "Get the current status and result of a podcast episode generation job.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "episode_id": {"type": "integer", "description": "Episode ID from generate_episode"},
            },
            "required": ["episode_id"],
        },
    },
}


# ── JSON-RPC helpers ──────────────────────────────────────────────────────────

def _ok(req_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str, data: Any = None) -> dict:
    error: dict = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": error}


# JSON-RPC error codes
PARSE_ERROR     = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS  = -32602
INTERNAL_ERROR  = -32603
UNAUTHORIZED    = -32000


# ── MCP method handlers ───────────────────────────────────────────────────────

def _handle_initialize(req_id: Any, _params: dict) -> dict:
    return _ok(req_id, {
        "protocolVersion": MCP_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    })


def _handle_tools_list(req_id: Any, _params: dict) -> dict:
    tools = [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]
    return _ok(req_id, {"tools": tools})


def _handle_tools_call(req_id: Any, params: dict, user: User, db: Session) -> dict:
    tool_name = params.get("name")
    tool_args = params.get("arguments", {})

    if tool_name not in TOOLS:
        return _err(req_id, METHOD_NOT_FOUND, f"Unknown tool: {tool_name}")

    try:
        result = TOOLS[tool_name]["handler"](tool_args, user, db)
        return _ok(req_id, {
            "content": [{"type": "text", "text": json.dumps(result, default=str)}],
            "isError": False,
        })
    except ValueError as exc:
        return _err(req_id, INVALID_PARAMS, str(exc))
    except Exception as exc:
        return _err(req_id, INTERNAL_ERROR, "Tool execution failed", str(exc))


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/mcp")
async def mcp_endpoint(request: Request, db: Session = Depends(get_db)):
    """
    MCP JSON-RPC 2.0 endpoint.

    Authentication: pass your CastAPI key in the X-API-Key header.

    Example — list tools:
        curl -X POST https://your-app.railway.app/mcp \\
          -H "Content-Type: application/json" \\
          -H "X-API-Key: msk_YOUR_KEY" \\
          -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

    Example — generate an episode:
        curl -X POST https://your-app.railway.app/mcp \\
          -H "Content-Type: application/json" \\
          -H "X-API-Key: msk_YOUR_KEY" \\
          -d '{
            "jsonrpc": "2.0", "id": 2,
            "method": "tools/call",
            "params": {
              "name": "generate_episode",
              "arguments": {"podcast_id": 1, "topic": "The future of AI in podcasting"}
            }
          }'
    """
    # Parse body
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            _err(None, PARSE_ERROR, "Parse error: invalid JSON"),
            status_code=200,  # JSON-RPC always returns 200
        )

    req_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params") or {}

    # initialize doesn't require auth
    if method == "initialize":
        return JSONResponse(_handle_initialize(req_id, params))

    # All other methods require auth
    api_key_value = request.headers.get("X-API-Key") or request.headers.get("x-api-key", "")
    user = _get_user_from_api_key(api_key_value, db)
    if user is None:
        return JSONResponse(
            _err(req_id, UNAUTHORIZED, "Invalid or missing API key"),
            status_code=200,
        )

    if method == "tools/list":
        return JSONResponse(_handle_tools_list(req_id, params))

    if method == "tools/call":
        return JSONResponse(_handle_tools_call(req_id, params, user, db))

    return JSONResponse(_err(req_id, METHOD_NOT_FOUND, f"Method not found: {method}"))
