"""Initial schema — create all tables.

Revision ID: 001
Revises:
Create Date: 2026-03-29 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("subscription_tier", sa.Enum("free", "pro", "enterprise", name="subscriptiontier"), nullable=True),
        sa.Column("subscription_status", sa.String(50), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("episodes_generated_this_month", sa.Integer(), nullable=True),
        sa.Column("api_calls_this_month", sa.Integer(), nullable=True),
        sa.Column("storage_used_mb", sa.Float(), nullable=True),
        sa.Column("default_voice_host_1", sa.String(255), nullable=True),
        sa.Column("default_voice_host_2", sa.String(255), nullable=True),
        sa.Column("default_tts_provider", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("prefix", sa.String(20), nullable=True),
        sa.Column("rate_limit_per_hour", sa.Integer(), nullable=True),
        sa.Column("calls_made_this_hour", sa.Integer(), nullable=True),
        sa.Column("last_reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_calls", sa.Integer(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "podcasts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("host_1_name", sa.String(100), nullable=True),
        sa.Column("host_2_name", sa.String(100), nullable=True),
        sa.Column("host_1_voice_id", sa.String(255), nullable=True),
        sa.Column("host_2_voice_id", sa.String(255), nullable=True),
        sa.Column("tts_provider", sa.String(50), nullable=True),
        sa.Column("elevenlabs_model", sa.String(100), nullable=True),
        sa.Column("openai_voice", sa.String(100), nullable=True),
        sa.Column("target_word_count", sa.Integer(), nullable=True),
        sa.Column("content_sources", sa.JSON(), nullable=True),
        sa.Column("custom_prompt_sections", sa.JSON(), nullable=True),
        sa.Column("transistor_show_id", sa.String(255), nullable=True),
        sa.Column("auto_publish", sa.Boolean(), nullable=True),
        sa.Column("total_episodes", sa.Integer(), nullable=True),
        sa.Column("total_storage_mb", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scripts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("plain_text", sa.Text(), nullable=True),
        sa.Column("template_type", sa.String(50), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("podcast_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("script", sa.JSON(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.String(1000), nullable=True),
        sa.Column("audio_duration_seconds", sa.Float(), nullable=True),
        sa.Column("audio_size_mb", sa.Float(), nullable=True),
        sa.Column("audio_storage_key", sa.String(500), nullable=True),
        sa.Column("transistor_episode_id", sa.String(255), nullable=True),
        sa.Column("publish_url", sa.String(1000), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_model_used", sa.String(100), nullable=True),
        sa.Column("ai_prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("ai_completion_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["podcast_id"], ["podcasts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "usage_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("podcast_id", sa.Integer(), nullable=True),
        sa.Column("episode_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("api_calls", sa.Integer(), nullable=True),
        sa.Column("storage_mb", sa.Float(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"]),
        sa.ForeignKeyConstraint(["podcast_id"], ["podcasts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("jobs")
    op.drop_table("usage_logs")
    op.drop_table("episodes")
    op.drop_table("scripts")
    op.drop_table("podcasts")
    op.drop_table("api_keys")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
