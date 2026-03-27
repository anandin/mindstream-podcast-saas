#!/usr/bin/env python3
"""
Mind Stream SaaS - Main Application
=====================================
Run: python -m saas.app

This combines the REST API with the podcast generation pipeline.
"""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import SaaS modules first
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from saas.api.main import app as api_app, get_db_session
from saas.db.models import (
    User, Podcast, Episode, APIKey, UsageLog, SubscriptionTier,
    check_user_limit, SUBSCRIPTION_LIMITS, init_db
)
from saas.auth.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from saas.dashboard.templates import get_dashboard_html, get_login_html

# Initialize database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db")
init_db(DATABASE_URL)

# Create main app
app = FastAPI(
    title="Mind Stream SaaS",
    description="AI-Powered Podcast Generation Platform",
    version="1.0.0"
)

# CORS - add middleware here since include_router drops middleware from api_app
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes - routes already have /api/v1 prefix
app.include_router(api_app.router)


# ── Static Files ───────────────────────────────────────────────────────────

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)


# ── Dashboard Routes ─────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to dashboard or login."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Mind Stream SaaS</title></head>
    <body>
        <script>window.location.href = '/dashboard';</script>
    </body>
    </html>
    """


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page."""
    return get_dashboard_html()


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login/Register page."""
    return get_login_html("login")


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """Registration page (shows register tab)."""
    return get_login_html("register")


@app.get("/api/docs", response_class=HTMLResponse)
async def api_docs():
    """Redirect to Swagger docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs", status_code=301)


# ── Error Handlers ───────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found(request, exc):
    return HTMLResponse("<h1>404 - Not Found</h1>", status_code=404)


@app.exception_handler(500)
async def server_error(request, exc):
    return HTMLResponse("<h1>500 - Server Error</h1>", status_code=500)


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
