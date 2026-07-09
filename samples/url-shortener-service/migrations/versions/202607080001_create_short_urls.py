"""create short urls

Revision ID: 202607080001
Revises:
Create Date: 2026-07-08 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607080001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "short_urls",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("target_url", sa.String(length=2048), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_short_urls")),
    )
    op.create_index(
        op.f("ix_short_urls_code"),
        "short_urls",
        ["code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_short_urls_code"), table_name="short_urls")
    op.drop_table("short_urls")
