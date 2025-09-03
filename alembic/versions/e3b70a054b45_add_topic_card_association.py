"""add topic card association

Revision ID: e3b70a054b45
Revises: 485135085582
Create Date: 2025-08-20 21:04:32.556327

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3b70a054b45"
down_revision: Union[str, Sequence[str], None] = "485135085582"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "topic_card_association",
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["cards.id"],
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.PrimaryKeyConstraint("topic_id", "card_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("topic_card_association")
