"""add_reminders_table

Revision ID: 4e7a8b9c2d5f
Revises: 3d8f9c2a1b4e
Create Date: 2025-11-21 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e7a8b9c2d5f'
down_revision: Union[str, Sequence[str], None] = '3d8f9c2a1b4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('reminders',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('reminders')