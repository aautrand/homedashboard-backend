"""Adding quizzes and tracking for them

Revision ID: 51d6e81eda9e
Revises: c566d09aef7c
Create Date: 2025-12-17 16:18:56.352372

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "51d6e81eda9e"
down_revision: Union[str, Sequence[str], None] = "c566d09aef7c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "quizzes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["cards.id"],
        ),
        sa.ForeignKeyConstraint(
            ["quiz_id"],
            ["quizzes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "quiz_answers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quiz_question_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("score", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["quiz_question_id"],
            ["quiz_questions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "cards", sa.Column("knowledge_level", sa.SmallInteger(), nullable=True)
    )
    op.add_column(
        "cards", sa.Column("consecutive_correct", sa.SmallInteger(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("cards", "consecutive_correct")
    op.drop_column("cards", "knowledge_level")
    op.drop_table("quiz_answers")
    op.drop_table("quiz_questions")
    op.drop_table("quizzes")
