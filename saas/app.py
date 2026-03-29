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
from fastapi.openapi.utils import get_openapi
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
from saas.dashboard.landing import get_landing_html
from saas.dashboard.castapi import get_castapi_html

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


# Custom OpenAPI schema: add security schemes so Swagger shows auth on all routes
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {})["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
    }
    schema["security"] = [{"BearerAuth": []}, {"ApiKeyAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi


# ── Static Files ───────────────────────────────────────────────────────────

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)


# ── Dashboard Routes ─────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """Mind Stream landing page."""
    return get_landing_html()


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


@app.get("/castapi", response_class=HTMLResponse)
async def castapi_page():
    """CastAPI developer portal."""
    return get_castapi_html()


@app.get("/api/docs", response_class=HTMLResponse)
async def api_docs():
    """Redirect to Swagger docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs", status_code=301)


# ── Error Handlers ───────────────────────────────────────────────────────

from fastapi.exceptions import HTTPException as FastAPIHTTPException


@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    return HTMLResponse(f"<h1>{exc.status_code} - Error</h1>", status_code=exc.status_code)


@app.exception_handler(404)
async def not_found(request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    return HTMLResponse("<h1>404 - Not Found</h1>", status_code=404)


@app.exception_handler(500)
async def server_error(request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Internal server error"}, status_code=500)
    return HTMLResponse("<h1>500 - Server Error</h1>", status_code=500)


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
