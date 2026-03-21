"""
REST API for SaaS podcast generator.
"""
import os
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from functools import wraps
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func
import jwt

from saas.db.models import (
    Base, User, Podcast, Episode, APIKey, UsageLog,
    SubscriptionTier, check_user_limit, SUBSCRIPTION_LIMITS, init_db
)
from saas.db import get_db_session_maker
from saas.auth.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, generate_api_key, hash_api_key, verify_api_key, TokenPayload
)


# Create FastAPI dependency for database sessions
def get_db():
    """FastAPI dependency for database sessions."""
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db")
    SessionLocal = get_db_session_maker(DATABASE_URL)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Alias for compatibility with route dependencies
get_db_session = get_db

# Initialize database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saas_podcast.db")
init_db(DATABASE_URL)

# Create FastAPI app
app = FastAPI(
    title="Mind the Gap SaaS API",
    description="Podcast generation API for SaaS",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Constants
API_SECRET = os.getenv("API_SECRET", "default-secret-change-in-production")


# ── Pydantic Models ───────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    company: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    company: Optional[str]
    subscription_tier: str
    subscription_status: str
    episodes_generated_this_month: int
    api_calls_this_month: int
    storage_used_mb: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    default_voice_host_1: Optional[str] = None
    default_voice_host_2: Optional[str] = None
    default_tts_provider: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class PodcastCreate(BaseModel):
    title: str
    description: Optional[str] = None
    language: str = "en"
    host_1_name: str = "Alex"
    host_2_name: str = "Maya"
    host_1_voice_id: Optional[str] = None
    host_2_voice_id: Optional[str] = None
    tts_provider: str = "elevenlabs"
    elevenlabs_model: str = "eleven_multilingual_v2"
    openai_voice: str = "alloy"
    target_word_count: int = 1500
    content_sources: List[str] = []
    custom_prompt_sections: dict = {}


class PodcastUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    host_1_name: Optional[str] = None
    host_2_name: Optional[str] = None
    host_1_voice_id: Optional[str] = None
    host_2_voice_id: Optional[str] = None
    tts_provider: Optional[str] = None
    elevenlabs_model: Optional[str] = None
    openai_voice: Optional[str] = None
    target_word_count: Optional[int] = None
    content_sources: Optional[List[str]] = None
    custom_prompt_sections: Optional[dict] = None
    auto_publish: Optional[bool] = None


class PodcastResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    language: str
    host_1_name: str
    host_2_name: str
    host_1_voice_id: Optional[str]
    host_2_voice_id: Optional[str]
    tts_provider: str
    elevenlabs_model: str
    openai_voice: str
    target_word_count: int
    content_sources: List[str]
    custom_prompt_sections: dict
    total_episodes: int
    total_storage_mb: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class EpisodeResponse(BaseModel):
    id: int
    podcast_id: int
    date: datetime
    title: Optional[str]
    description: Optional[str]
    audio_url: Optional[str]
    audio_duration_seconds: Optional[float]
    audio_size_mb: Optional[float]
    status: str
    error_message: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class GenerateEpisodeRequest(BaseModel):
    podcast_id: int
    date: Optional[str] = None  # YYYY-MM-DD format
    script_only: bool = False
    no_publish: bool = False


class APIKeyCreate(BaseModel):
    name: str
    rate_limit_per_hour: int = 100
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    rate_limit_per_hour: int
    total_calls: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    tier: str
    status: str
    limits: dict
    current_usage: dict


class UsageStatsResponse(BaseModel):
    episodes_this_month: int
    api_calls_this_month: int
    storage_used_mb: float
    total_episodes: int
    total_cost_usd: float


# ── Dependencies ───────────────────────────────────────────────────────────

def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db_session)
) -> User:
    """Get the current authenticated user."""
    # Check for API key first
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        key_hash = hash_api_key(api_key_header)
        api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.is_active == True).first()
        if api_key:
            # Check if API key has expired
            now = datetime.now(timezone.utc)
            if api_key.expires_at and now > api_key.expires_at:
                raise HTTPException(status_code=401, detail="API key expired")
            
            # Update rate limiting
            if not api_key.last_reset_at or (now - api_key.last_reset_at) > timedelta(hours=1):
                api_key.calls_made_this_hour = 0
                api_key.last_reset_at = now
            
            if api_key.calls_made_this_hour >= api_key.rate_limit_per_hour:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            api_key.calls_made_this_hour += 1
            api_key.total_calls += 1
            api_key.last_used_at = now
            db.commit()
            
            # Get user and check if active
            user = db.query(User).filter(User.id == api_key.user_id, User.is_active == True).first()
            if not user:
                raise HTTPException(status_code=401, detail="User account is disabled")
            
            # Update user API calls and check monthly limit
            can_proceed, message = check_user_limit(user, "api_calls")
            if not can_proceed:
                raise HTTPException(status_code=403, detail=message)
            
            user.api_calls_this_month += 1
            db.commit()
            return user
    
    # Check for JWT token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = db.query(User).filter(User.id == payload.get("user_id"), User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or account disabled")
    
    return user


def require_tier(tier: SubscriptionTier):
    """Dependency to require a specific subscription tier."""
    def checker(user: User = Depends(get_current_user)) -> User:
        tier_order = [SubscriptionTier.FREE, SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]
        user_tier_idx = tier_order.index(user.subscription_tier)
        required_tier_idx = tier_order.index(tier)
        
        if user_tier_idx < required_tier_idx:
            raise HTTPException(
                status_code=403,
                detail=f"Requires {tier.value} subscription or higher"
            )
        return user
    return checker


# ── Auth Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/v1/auth/register", response_model=TokenResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db_session)):
    """Register a new user account."""
    # Check if user exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        company=user_data.company,
        subscription_tier=SubscriptionTier.FREE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create tokens
    access_token = create_access_token({"user_id": user.id, "email": user.email})
    refresh_token = create_refresh_token({"user_id": user.id, "email": user.email})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db_session)):
    """Login to existing account."""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token({"user_id": user.id, "email": user.email})
    refresh_token = create_refresh_token({"user_id": user.id, "email": user.email})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@app.post("/api/v1/auth/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db_session)):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = db.query(User).filter(User.id == payload.get("user_id"), User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or account disabled")
    
    access_token = create_access_token({"user_id": user.id, "email": user.email})
    new_refresh_token = create_refresh_token({"user_id": user.id, "email": user.email})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user)
    )


# ── User Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/v1/user/me", response_model=UserResponse)
def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse.model_validate(user)


@app.put("/api/v1/user/me", response_model=UserResponse)
def update_user(
    updates: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update current user information."""
    if updates.name is not None:
        user.name = updates.name
    if updates.company is not None:
        user.company = updates.company
    if updates.default_voice_host_1 is not None:
        user.default_voice_host_1 = updates.default_voice_host_1
    if updates.default_voice_host_2 is not None:
        user.default_voice_host_2 = updates.default_voice_host_2
    if updates.default_tts_provider is not None:
        user.default_tts_provider = updates.default_tts_provider
    
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@app.get("/api/v1/user/subscription", response_model=SubscriptionResponse)
def get_subscription(user: User = Depends(get_current_user)):
    """Get subscription information and limits."""
    limits = SUBSCRIPTION_LIMITS[user.subscription_tier]
    return SubscriptionResponse(
        tier=user.subscription_tier.value,
        status=user.subscription_status,
        limits={
            "episodes_per_month": limits["episodes_per_month"],
            "api_calls_per_month": limits["api_calls_per_month"],
            "storage_mb": limits["storage_mb"],
            "podcasts": limits["podcasts"],
            "custom_prompts": limits["custom_prompts"],
            "api_access": limits["api_access"],
            "auto_publish": limits["auto_publish"],
        },
        current_usage={
            "episodes_this_month": user.episodes_generated_this_month,
            "api_calls_this_month": user.api_calls_this_month,
            "storage_used_mb": user.storage_used_mb,
        }
    )


@app.get("/api/v1/user/usage", response_model=UsageStatsResponse)
def get_usage_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Get detailed usage statistics."""
    # Get total episodes
    total_episodes = db.query(Episode).join(Podcast).filter(Podcast.user_id == user.id).count()
    
    # Get total cost
    total_cost = db.query(UsageLog).filter(
        UsageLog.user_id == user.id,
        UsageLog.action == "episode_generation"
    ).with_entities(func.sum(UsageLog.cost_usd)).scalar() or 0
    
    return UsageStatsResponse(
        episodes_this_month=user.episodes_generated_this_month,
        api_calls_this_month=user.api_calls_this_month,
        storage_used_mb=user.storage_used_mb,
        total_episodes=total_episodes,
        total_cost_usd=float(total_cost)
    )


# ── Podcast Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/v1/podcasts", response_model=List[PodcastResponse])
def list_podcasts(user: User = Depends(get_current_user), db: Session = Depends(get_db_session)):
    """List all podcasts owned by the user."""
    podcasts = db.query(Podcast).filter(Podcast.user_id == user.id, Podcast.is_active == True).all()
    return [PodcastResponse.model_validate(p) for p in podcasts]


@app.post("/api/v1/podcasts", response_model=PodcastResponse, status_code=201)
def create_podcast(
    podcast_data: PodcastCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create a new podcast."""
    # Check podcast limit
    limits = SUBSCRIPTION_LIMITS[user.subscription_tier]
    podcast_count = db.query(Podcast).filter(Podcast.user_id == user.id, Podcast.is_active == True).count()
    
    if limits["podcasts"] > 0 and podcast_count >= limits["podcasts"]:
        raise HTTPException(
            status_code=403,
            detail=f"Podcast limit reached ({podcast_count}/{limits['podcasts']}). Upgrade to create more."
        )
    
    podcast = Podcast(
        user_id=user.id,
        title=podcast_data.title,
        description=podcast_data.description,
        language=podcast_data.language,
        host_1_name=podcast_data.host_1_name,
        host_2_name=podcast_data.host_2_name,
        host_1_voice_id=podcast_data.host_1_voice_id or user.default_voice_host_1,
        host_2_voice_id=podcast_data.host_2_voice_id or user.default_voice_host_2,
        tts_provider=podcast_data.tts_provider,
        elevenlabs_model=podcast_data.elevenlabs_model,
        openai_voice=podcast_data.openai_voice,
        target_word_count=podcast_data.target_word_count,
        content_sources=podcast_data.content_sources,
        custom_prompt_sections=podcast_data.custom_prompt_sections,
    )
    db.add(podcast)
    db.commit()
    db.refresh(podcast)
    return PodcastResponse.model_validate(podcast)


@app.get("/api/v1/podcasts/{podcast_id}", response_model=PodcastResponse)
def get_podcast(podcast_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Get a specific podcast."""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id, Podcast.user_id == user.id, Podcast.is_active == True).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return PodcastResponse.model_validate(podcast)


@app.put("/api/v1/podcasts/{podcast_id}", response_model=PodcastResponse)
def update_podcast(
    podcast_id: int,
    updates: PodcastUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update a podcast."""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id, Podcast.user_id == user.id, Podcast.is_active == True).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    
    # Check tier restrictions for Pro/Enterprise features
    tier_restricted_fields = ["custom_prompt_sections", "auto_publish"]
    updates_dict = updates.model_dump(exclude_unset=True)
    
    for field in tier_restricted_fields:
        if field in updates_dict and updates_dict[field]:
            if user.subscription_tier == SubscriptionTier.FREE:
                raise HTTPException(
                    status_code=403,
                    detail=f"Feature '{field}' requires Pro or Enterprise tier"
                )
    
    # Update fields
    for field, value in updates_dict.items():
        setattr(podcast, field, value)
    
    podcast.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(podcast)
    return PodcastResponse.model_validate(podcast)


@app.delete("/api/v1/podcasts/{podcast_id}")
def delete_podcast(podcast_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Delete a podcast (soft delete)."""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id, Podcast.user_id == user.id, Podcast.is_active == True).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    
    podcast.is_active = False
    podcast.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Podcast deleted successfully"}


# ── Episode Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/v1/podcasts/{podcast_id}/episodes", response_model=List[EpisodeResponse])
def list_episodes(
    podcast_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """List all episodes for a podcast."""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id, Podcast.user_id == user.id, Podcast.is_active == True).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    
    episodes = db.query(Episode).filter(Episode.podcast_id == podcast_id).order_by(Episode.date.desc()).all()
    return [EpisodeResponse.model_validate(e) for e in episodes]


@app.get("/api/v1/episodes/{episode_id}", response_model=EpisodeResponse)
def get_episode(episode_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Get a specific episode."""
    episode = db.query(Episode).join(Podcast).filter(
        Episode.id == episode_id,
        Podcast.user_id == user.id
    ).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return EpisodeResponse.model_validate(episode)


@app.post("/api/v1/episodes/generate", response_model=EpisodeResponse)
def generate_episode(
    request: GenerateEpisodeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Generate a new episode."""
    # Get podcast
    podcast = db.query(Podcast).filter(
        Podcast.id == request.podcast_id,
        Podcast.user_id == user.id,
        Podcast.is_active == True
    ).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    
    # Check episode limit
    can_proceed, message = check_user_limit(user, "episodes")
    if not can_proceed:
        raise HTTPException(status_code=403, detail=message)
    
    # Check storage limit
    can_proceed, message = check_user_limit(user, "storage")
    if not can_proceed and not request.script_only:
        raise HTTPException(status_code=403, detail=message)
    
    # Parse date
    if request.date:
        try:
            ep_date = datetime.strptime(request.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        ep_date = datetime.now(timezone.utc)
    
    # Create episode record
    episode = Episode(
        podcast_id=podcast.id,
        date=ep_date,
        status="generating",
    )
    db.add(episode)
    db.commit()
    db.refresh(episode)
    
    # TODO: Integrate with the actual podcast generation pipeline
    # For now, return a placeholder response
    episode.status = "ready" if request.script_only else "ready"
    episode.title = f"Episode - {ep_date.strftime('%Y-%m-%d')}"
    db.commit()
    
    # Update user usage
    user.episodes_generated_this_month += 1
    db.commit()
    
    return EpisodeResponse.model_validate(episode)


# ── API Key Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/v1/api-keys", response_model=List[APIKeyResponse])
def list_api_keys(user: User = Depends(require_tier(SubscriptionTier.PRO)), db: Session = Depends(get_db_session)):
    """List all API keys for the user."""
    keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
    return [APIKeyResponse.model_validate(k) for k in keys]


@app.post("/api/v1/api-keys", response_model=dict)
def create_api_key(
    key_data: APIKeyCreate,
    user: User = Depends(require_tier(SubscriptionTier.PRO)),
    db: Session = Depends(get_db_session)
):
    """Create a new API key."""
    full_key, key_hash, prefix = generate_api_key()
    
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=key_data.expires_in_days)
    
    api_key = APIKey(
        user_id=user.id,
        key_hash=key_hash,
        prefix=prefix,
        name=key_data.name,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    
    return {
        "id": api_key.id,
        "key": full_key,  # Only returned once!
        "name": api_key.name,
        "prefix": prefix,
        "rate_limit_per_hour": api_key.rate_limit_per_hour,
        "expires_at": expires_at,
    }


@app.delete("/api/v1/api-keys/{key_id}")
def delete_api_key(key_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Delete an API key."""
    api_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user.id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.is_active = False
    db.commit()
    return {"message": "API key deleted successfully"}


# ── Health Check ────────────────────────────────────────────────────────────

@app.get("/healthz")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "mind-the-gap-saas"}


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
