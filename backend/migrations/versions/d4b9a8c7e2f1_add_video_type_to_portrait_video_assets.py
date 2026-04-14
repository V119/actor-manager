"""Add video type to portrait video assets

Revision ID: d4b9a8c7e2f1
Revises: c7b1d5a8e4f2
Create Date: 2026-04-14 23:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d4b9a8c7e2f1"
down_revision = "c7b1d5a8e4f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "portraitvideoassetmodel",
        sa.Column("video_type", sa.String(), nullable=True, server_default="intro"),
    )
    op.execute("UPDATE portraitvideoassetmodel SET video_type = 'intro' WHERE video_type IS NULL")
    op.alter_column(
        "portraitvideoassetmodel",
        "video_type",
        existing_type=sa.String(),
        nullable=False,
        server_default="intro",
    )

    op.drop_index(
        "uq_portraitvideoassetmodel_one_current_per_user_actor",
        table_name="portraitvideoassetmodel",
    )
    op.drop_index(
        "ix_portraitvideoassetmodel_user_actor_is_current",
        table_name="portraitvideoassetmodel",
    )

    op.create_index(
        "ix_portraitvideoassetmodel_user_actor_type_is_current",
        "portraitvideoassetmodel",
        ["user_id", "actor_id", "video_type", "is_current"],
        unique=False,
    )
    op.create_index(
        "uq_portraitvideoassetmodel_one_current_per_user_actor_type",
        "portraitvideoassetmodel",
        ["user_id", "actor_id", "video_type"],
        unique=True,
        postgresql_where=sa.text("is_current = TRUE"),
    )
    op.create_index(
        "ix_portraitvideoassetmodel_actor_user_video_type_created_at",
        "portraitvideoassetmodel",
        ["actor_id", "user_id", "video_type", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_portraitvideoassetmodel_actor_user_video_type_created_at",
        table_name="portraitvideoassetmodel",
    )
    op.drop_index(
        "uq_portraitvideoassetmodel_one_current_per_user_actor_type",
        table_name="portraitvideoassetmodel",
    )
    op.drop_index(
        "ix_portraitvideoassetmodel_user_actor_type_is_current",
        table_name="portraitvideoassetmodel",
    )

    op.create_index(
        "ix_portraitvideoassetmodel_user_actor_is_current",
        "portraitvideoassetmodel",
        ["user_id", "actor_id", "is_current"],
        unique=False,
    )
    op.create_index(
        "uq_portraitvideoassetmodel_one_current_per_user_actor",
        "portraitvideoassetmodel",
        ["user_id", "actor_id"],
        unique=True,
        postgresql_where=sa.text("is_current = TRUE"),
    )

    op.drop_column("portraitvideoassetmodel", "video_type")
