"""Add portrait guidance samples

Revision ID: c7b1d5a8e4f2
Revises: a6d9e3f2c1b4
Create Date: 2026-04-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c7b1d5a8e4f2"
down_revision = "a6d9e3f2c1b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portraitguidancesamplemodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("view_angle", sa.String(), nullable=False),
        sa.Column("bucket_name", sa.String(), nullable=False),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("source_filename", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("view_angle"),
    )
    op.create_index(
        "ix_portraitguidancesamplemodel_view_angle",
        "portraitguidancesamplemodel",
        ["view_angle"],
        unique=True,
    )
    op.create_index(
        "ix_portraitguidancesamplemodel_updated_at",
        "portraitguidancesamplemodel",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_portraitguidancesamplemodel_updated_at", table_name="portraitguidancesamplemodel")
    op.drop_index("ix_portraitguidancesamplemodel_view_angle", table_name="portraitguidancesamplemodel")
    op.drop_table("portraitguidancesamplemodel")
