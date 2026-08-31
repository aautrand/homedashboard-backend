"""add_quotes_table

Revision ID: d4e5f6a7b8c9
Revises: 0aac49d00b59
Create Date: 2026-08-21 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "0aac49d00b59"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pinned_date", sa.Date(), nullable=True),
        sa.Column("last_shown_date", sa.Date(), nullable=True),
        sa.Column("times_shown", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quotes_pinned", "quotes", ["pinned"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_quotes_pinned", table_name="quotes")
    op.drop_table("quotes")
