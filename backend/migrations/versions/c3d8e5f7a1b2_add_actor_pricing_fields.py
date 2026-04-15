"""Add actor pricing fields

Revision ID: c3d8e5f7a1b2
Revises: b4e7c1d9f2a3
Create Date: 2026-04-16 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3d8e5f7a1b2"
down_revision = "b4e7c1d9f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "actormodel",
        sa.Column("pricing_unit", sa.String(), nullable=False, server_default="project"),
    )
    op.add_column(
        "actormodel",
        sa.Column("pricing_amount", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("actormodel", "pricing_amount")
    op.drop_column("actormodel", "pricing_unit")
