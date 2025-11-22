"""add_study_fields_to_subjects

Revision ID: 6g9c0b1d4f7h
Revises: 5f8b9a0c3e6d
Create Date: 2025-11-21 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6g9c0b1d4f7h'
down_revision: Union[str, Sequence[str], None] = '5f8b9a0c3e6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('subjects', sa.Column('created_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('subjects', sa.Column('updated_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('subjects', sa.Column('last_shown_date', sa.Date(), nullable=True))
    op.add_column('subjects', sa.Column('times_shown', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('subjects', sa.Column('study_active', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('subjects', 'study_active')
    op.drop_column('subjects', 'times_shown')
    op.drop_column('subjects', 'last_shown_date')
    op.drop_column('subjects', 'updated_date')
    op.drop_column('subjects', 'created_date')