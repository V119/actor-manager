"""Add portrait video assets table

Revision ID: 7c5f2efaf8c1
Revises: e1b3a913f2bf
Create Date: 2026-04-12 17:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7c5f2efaf8c1"
down_revision = "e1b3a913f2bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portraitvideoassetmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bucket_name", sa.String(), nullable=False),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("video_url", sa.String(), nullable=False),
        sa.Column("source_filename", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_portraitvideoassetmodel_actor_user_created_at",
        "portraitvideoassetmodel",
        ["actor_id", "user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraitvideoassetmodel_created_at",
        "portraitvideoassetmodel",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_portraitvideoassetmodel_created_at", table_name="portraitvideoassetmodel")
    op.drop_index("ix_portraitvideoassetmodel_actor_user_created_at", table_name="portraitvideoassetmodel")
    op.drop_table("portraitvideoassetmodel")
