"""Add company intro field to user model

Revision ID: a6d9e3f2c1b4
Revises: f1c6d4b8a9e2
Create Date: 2026-04-13 17:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a6d9e3f2c1b4"
down_revision = "f1c6d4b8a9e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usermodel",
        sa.Column("company_intro", sa.Text(), nullable=True, server_default=""),
    )
    op.execute("UPDATE usermodel SET company_intro = '' WHERE company_intro IS NULL")
    op.alter_column(
        "usermodel",
        "company_intro",
        existing_type=sa.Text(),
        nullable=False,
        server_default="",
    )


def downgrade() -> None:
    op.drop_column("usermodel", "company_intro")
