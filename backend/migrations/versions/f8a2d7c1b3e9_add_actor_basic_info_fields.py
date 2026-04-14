"""Add actor basic profile fields

Revision ID: f8a2d7c1b3e9
Revises: d4b9a8c7e2f1
Create Date: 2026-04-15 00:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f8a2d7c1b3e9"
down_revision = "d4b9a8c7e2f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "actormodel",
        sa.Column("hometown", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "actormodel",
        sa.Column("weight_kg", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "actormodel",
        sa.Column("bust_cm", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "actormodel",
        sa.Column("waist_cm", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "actormodel",
        sa.Column("hip_cm", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "actormodel",
        sa.Column("shoe_size", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "actormodel",
        sa.Column("acting_requirements", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "actormodel",
        sa.Column("rejected_requirements", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "actormodel",
        sa.Column("availability_note", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("actormodel", "availability_note")
    op.drop_column("actormodel", "rejected_requirements")
    op.drop_column("actormodel", "acting_requirements")
    op.drop_column("actormodel", "shoe_size")
    op.drop_column("actormodel", "hip_cm")
    op.drop_column("actormodel", "waist_cm")
    op.drop_column("actormodel", "bust_cm")
    op.drop_column("actormodel", "weight_kg")
    op.drop_column("actormodel", "hometown")
