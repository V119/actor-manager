"""Add portrait audio assets table

Revision ID: b4e7c1d9f2a3
Revises: a1c9e4d2f6b7
Create Date: 2026-04-15 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b4e7c1d9f2a3"
down_revision = "a1c9e4d2f6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portraitaudioassetmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
        sa.Column("bucket_name", sa.String(), nullable=False),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("audio_url", sa.String(), nullable=False),
        sa.Column("source_filename", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_portraitaudioassetmodel_actor_user_is_published_created_at",
        "portraitaudioassetmodel",
        ["actor_id", "user_id", "is_published", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraitaudioassetmodel_is_published",
        "portraitaudioassetmodel",
        ["is_published"],
        unique=False,
    )
    op.create_index(
        "ix_portraitaudioassetmodel_superseded_at",
        "portraitaudioassetmodel",
        ["superseded_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraitaudioassetmodel_created_at",
        "portraitaudioassetmodel",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_portraitaudioassetmodel_created_at", table_name="portraitaudioassetmodel")
    op.drop_index("ix_portraitaudioassetmodel_superseded_at", table_name="portraitaudioassetmodel")
    op.drop_index("ix_portraitaudioassetmodel_is_published", table_name="portraitaudioassetmodel")
    op.drop_index(
        "ix_portraitaudioassetmodel_actor_user_is_published_created_at",
        table_name="portraitaudioassetmodel",
    )
    op.drop_table("portraitaudioassetmodel")
