"""Add Grow Layer columns to episodes table.

Revision ID: 003
Revises: 002
Create Date: 2026-03-29 02:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("episodes", sa.Column("seo_title", sa.String(500), nullable=True))
    op.add_column("episodes", sa.Column("show_notes", sa.Text(), nullable=True))
    op.add_column("episodes", sa.Column("audiogram_url", sa.String(1000), nullable=True))
    op.add_column("episodes", sa.Column("audiogram_status", sa.String(20), nullable=True, server_default="none"))


def downgrade() -> None:
    op.drop_column("episodes", "audiogram_status")
    op.drop_column("episodes", "audiogram_url")
    op.drop_column("episodes", "show_notes")
    op.drop_column("episodes", "seo_title")
