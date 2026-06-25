"""add_device_events_table

Revision ID: 0aac49d00b59
Revises: 60a5a51e5bf7
Create Date: 2026-05-29 08:46:54.540121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0aac49d00b59'
down_revision: Union[str, Sequence[str], None] = '60a5a51e5bf7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'device_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('device_id', sa.Text(), nullable=False),
        sa.Column(
            'recorded_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('device_events_pkey')),
    )
    op.create_index(
        op.f('ix_device_events_device_id'), 'device_events', ['device_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_device_events_device_id'), table_name='device_events')
    op.drop_table('device_events')
