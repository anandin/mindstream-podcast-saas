"""
Database models for SaaS podcast generator.
"""
from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime,
    Boolean, Float, ForeignKey, Enum, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum

Base = declarative_base()


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    company = Column(String(255))
    
    # Subscription
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_status = Column(String(50), default="active")  # active, cancelled, past_due
    stripe_customer_id = Column(String(255))
    subscription_expires_at = Column(DateTime(timezone=True))
    
    # Usage tracking
    episodes_generated_this_month = Column(Integer, default=0)
    api_calls_this_month = Column(Integer, default=0)
    storage_used_mb = Column(Float, default=0)
    
    # Settings
    default_voice_host_1 = Column(String(255), default="21m00Tcm4TlvDq8ikWAM")
    default_voice_host_2 = Column(String(255), default="pNInz6obpgDQGcFmaJgB")
    default_tts_provider = Column(String(50), default="minimax")  # minimax, elevenlabs, openai
    
    # API keys
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    # Podcasts owned by this user
    podcasts = relationship("Podcast", back_populates="owner", cascade="all, delete-orphan")
    
    # Scripts owned by this user
    scripts = relationship("Script", back_populates="owner", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    prefix = Column(String(20))  # First 8 chars for display
    
    # Rate limiting
    rate_limit_per_hour = Column(Integer, default=100)
    calls_made_this_hour = Column(Integer, default=0)
    last_reset_at = Column(DateTime(timezone=True))
    
    # Usage tracking
    total_calls = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    
    user = relationship("User", back_populates="api_keys")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Podcast(Base):
    __tablename__ = "podcasts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Identity
    title = Column(String(255), nullable=False)
    description = Column(Text)
    language = Column(String(10), default="en")
    
    # Hosts
    host_1_name = Column(String(100), default="Alex")
    host_2_name = Column(String(100), default="Maya")
    host_1_voice_id = Column(String(255))
    host_2_voice_id = Column(String(255))
    
    # TTS settings
    tts_provider = Column(String(50), default="minimax")  # minimax, elevenlabs, openai
    elevenlabs_model = Column(String(100), default="eleven_multilingual_v2")
    openai_voice = Column(String(100), default="alloy")
    
    # Content settings
    target_word_count = Column(Integer, default=1500)
    content_sources = Column(JSON, default=list)  # RSS feeds, etc.
    custom_prompt_sections = Column(JSON, default=dict)
    
    # Publishing (optional - for Transistor.fm integration)
    transistor_show_id = Column(String(255))
    auto_publish = Column(Boolean, default=False)
    
    # Usage tracking
    total_episodes = Column(Integer, default=0)
    total_storage_mb = Column(Float, default=0)
    
    # Relationships
    owner = relationship("User", back_populates="podcasts")
    episodes = relationship("Episode", back_populates="podcast", cascade="all, delete-orphan")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)


class Script(Base):
    """Script model for ScriptFlow - stores script content before episode generation."""
    __tablename__ = "scripts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Script data
    title = Column(String(500), nullable=False)
    content = Column(Text)  # HTML content from WYSIWYG
    plain_text = Column(Text)  # Plain text for TTS
    template_type = Column(String(50))  # interview, solo, news, tutorial
    
    # Versioning
    version = Column(Integer, default=1)
    
    # Relationships
    owner = relationship("User", back_populates="scripts")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Episode(Base):
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True)
    podcast_id = Column(Integer, ForeignKey("podcasts.id"), nullable=False)
    
    # Episode data
    date = Column(DateTime(timezone=True), nullable=False)
    title = Column(String(500))
    description = Column(Text)
    script = Column(JSON)  # Full script with dialogue
    transcript = Column(Text)
    
    # Audio
    audio_url = Column(String(1000))
    audio_duration_seconds = Column(Float)
    audio_size_mb = Column(Float)
    audio_storage_key = Column(String(500))  # S3/local path
    
    # Publishing
    transistor_episode_id = Column(String(255))
    publish_url = Column(String(1000))
    published_at = Column(DateTime(timezone=True))
    
    # AI usage tracking
    ai_model_used = Column(String(100))
    ai_prompt_tokens = Column(Integer)
    ai_completion_tokens = Column(Integer)
    estimated_cost_usd = Column(Float)
    
    # Status
    status = Column(String(50), default="draft")  # draft, generating, ready, published, failed
    error_message = Column(Text)
    
    # Relationships
    podcast = relationship("Podcast", back_populates="episodes")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class UsageLog(Base):
    """Track API and generation usage for billing/analytics."""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    podcast_id = Column(Integer, ForeignKey("podcasts.id"))
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    
    # Usage details
    action = Column(String(100), nullable=False)  # episode_generation, api_call, storage
    resource_type = Column(String(50))  # episode, api_key, storage
    resource_id = Column(Integer)
    
    # Metrics
    tokens_used = Column(Integer, default=0)
    api_calls = Column(Integer, default=1)
    storage_mb = Column(Float, default=0)
    cost_usd = Column(Float, default=0)
    
    # Metadata (use extra_data to avoid SQLAlchemy conflict)
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Job(Base):
    """Background job queue for async processing tasks."""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(50), nullable=False)  # generate_episode, process_memo, deliver_webhook, grow
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="queued")  # queued|running|done|failed
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    scheduled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error = Column(Text)
    result = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# Database setup
def get_engine(database_url: str = "sqlite:///./saas.db"):
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        echo=False
    )


def init_db(database_url: str = "sqlite:///./saas.db"):
    """Initialize database tables."""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(database_url: str = "sqlite:///./saas.db"):
    """Get a database session."""
    engine = get_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()


# Subscription limits
SUBSCRIPTION_LIMITS = {
    SubscriptionTier.FREE: {
        "episodes_per_month": 3,
        "api_calls_per_month": 100,
        "storage_mb": 100,
        "podcasts": 1,
        "custom_prompts": False,
        "api_access": False,
        "auto_publish": False,
    },
    SubscriptionTier.PRO: {
        "episodes_per_month": 30,
        "api_calls_per_month": 5000,
        "storage_mb": 1000,
        "podcasts": 5,
        "custom_prompts": True,
        "api_access": True,
        "auto_publish": True,
    },
    SubscriptionTier.ENTERPRISE: {
        "episodes_per_month": -1,  # Unlimited
        "api_calls_per_month": -1,
        "storage_mb": 10000,
        "podcasts": -1,
        "custom_prompts": True,
        "api_access": True,
        "auto_publish": True,
    },
}


def check_user_limit(user: User, resource: str) -> tuple[bool, str]:
    """Check if user has exceeded their subscription limit."""
    limits = SUBSCRIPTION_LIMITS.get(user.subscription_tier, SUBSCRIPTION_LIMITS[SubscriptionTier.FREE])
    
    if resource == "episodes":
        limit = limits["episodes_per_month"]
        current = user.episodes_generated_this_month
        if limit > 0 and current >= limit:
            return False, f"Episode limit reached ({current}/{limit}). Upgrade to Pro for more."
    
    elif resource == "api_calls":
        limit = limits["api_calls_per_month"]
        current = user.api_calls_this_month
        if limit > 0 and current >= limit:
            return False, f"API call limit reached ({current}/{limit}). Upgrade to Pro for more."
    
    elif resource == "storage":
        limit = limits["storage_mb"]
        current = user.storage_used_mb
        if limit > 0 and current >= limit:
            return False, f"Storage limit reached ({current:.1f}MB/{limit}MB). Upgrade to Pro for more."
    
    elif resource == "podcasts":
        # This would need to be checked separately with a count query
        pass
    
    return True, "OK"
