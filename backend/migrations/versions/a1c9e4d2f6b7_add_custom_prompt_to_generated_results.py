"""Add custom prompt field for generated style results

Revision ID: a1c9e4d2f6b7
Revises: f8a2d7c1b3e9
Create Date: 2026-04-15 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1c9e4d2f6b7"
down_revision = "f8a2d7c1b3e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generatedresultmodel",
        sa.Column("custom_prompt", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("generatedresultmodel", "custom_prompt")
