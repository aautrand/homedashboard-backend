"""add_last_shown_date_to_reminders

Revision ID: 5f8b9a0c3e6d
Revises: 4e7a8b9c2d5f
Create Date: 2025-11-21 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f8b9a0c3e6d'
down_revision: Union[str, Sequence[str], None] = '4e7a8b9c2d5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('reminders', sa.Column('last_shown_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reminders', 'last_shown_date')