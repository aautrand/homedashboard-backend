"""add_grokked_field_to_cards

Revision ID: c566d09aef7c
Revises: 6g9c0b1d4f7h
Create Date: 2025-11-25 17:01:32.186082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c566d09aef7c'
down_revision: Union[str, Sequence[str], None] = '6g9c0b1d4f7h'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('cards', sa.Column('grokked', sa.Boolean(), nullable=False, server_default=sa.false()))
    


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('cards', 'grokked')
