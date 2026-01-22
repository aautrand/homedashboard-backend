"""add_always_show_to_subjects

Revision ID: 7h0d1c2e5g8i
Revises: 51d6e81eda9e
Create Date: 2025-01-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7h0d1c2e5g8i'
down_revision: Union[str, Sequence[str], None] = '51d6e81eda9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('subjects', sa.Column('always_show', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('subjects', 'always_show')