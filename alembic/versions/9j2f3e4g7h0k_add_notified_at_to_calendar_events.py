"""add_notified_at_to_calendar_events

Revision ID: 9j2f3e4g7h0k
Revises: 8i1e2d3f6g9j
Create Date: 2025-01-14 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9j2f3e4g7h0k'
down_revision: Union[str, Sequence[str], None] = '8i1e2d3f6g9j'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add notified_at column to track when event notifications were printed."""
    op.add_column('calendar_events',
        sa.Column('notified_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Remove notified_at column."""
    op.drop_column('calendar_events', 'notified_at')