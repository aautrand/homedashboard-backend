"""add_calendar_events_table

Revision ID: 8i1e2d3f6g9j
Revises: 7h0d1c2e5g8i
Create Date: 2025-01-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8i1e2d3f6g9j'
down_revision: Union[str, Sequence[str], None] = '7h0d1c2e5g8i'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('calendar_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uid', sa.Text(), nullable=False),
        sa.Column('calendar', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('recurring', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_synced', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uid')
    )
    op.create_index('ix_calendar_events_start_time', 'calendar_events', ['start_time'])
    op.create_index('ix_calendar_events_calendar', 'calendar_events', ['calendar'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_calendar_events_calendar', table_name='calendar_events')
    op.drop_index('ix_calendar_events_start_time', table_name='calendar_events')
    op.drop_table('calendar_events')