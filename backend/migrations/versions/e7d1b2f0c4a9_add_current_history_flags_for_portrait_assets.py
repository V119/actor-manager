"""Add current/history flags for portrait sessions and videos

Revision ID: e7d1b2f0c4a9
Revises: b2f4a6c1d9e7
Create Date: 2026-04-12 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e7d1b2f0c4a9"
down_revision = "b2f4a6c1d9e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("is_current", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
    )

    op.add_column(
        "portraitvideoassetmodel",
        sa.Column("is_current", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "portraitvideoassetmodel",
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
    )

    # Backfill sessions: mark only the latest row (user_id, actor_id) as current.
    op.execute("UPDATE portraituploadsessionmodel SET is_current = FALSE")
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY user_id, actor_id
                       ORDER BY created_at DESC, id DESC
                   ) AS rn
            FROM portraituploadsessionmodel
        )
        UPDATE portraituploadsessionmodel s
        SET is_current = CASE WHEN ranked.rn = 1 THEN TRUE ELSE FALSE END,
            superseded_at = CASE WHEN ranked.rn = 1 THEN NULL ELSE NOW() END
        FROM ranked
        WHERE s.id = ranked.id
        """
    )

    # Backfill videos: mark only the latest row (user_id, actor_id) as current.
    op.execute("UPDATE portraitvideoassetmodel SET is_current = FALSE")
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY user_id, actor_id
                       ORDER BY created_at DESC, id DESC
                   ) AS rn
            FROM portraitvideoassetmodel
        )
        UPDATE portraitvideoassetmodel v
        SET is_current = CASE WHEN ranked.rn = 1 THEN TRUE ELSE FALSE END,
            superseded_at = CASE WHEN ranked.rn = 1 THEN NULL ELSE NOW() END
        FROM ranked
        WHERE v.id = ranked.id
        """
    )

    op.alter_column(
        "portraituploadsessionmodel",
        "is_current",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.true(),
    )
    op.alter_column(
        "portraitvideoassetmodel",
        "is_current",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.true(),
    )

    op.create_index(
        "ix_portraituploadsessionmodel_user_actor_is_current",
        "portraituploadsessionmodel",
        ["user_id", "actor_id", "is_current"],
        unique=False,
    )
    op.create_index(
        "ix_portraituploadsessionmodel_superseded_at",
        "portraituploadsessionmodel",
        ["superseded_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraitvideoassetmodel_user_actor_is_current",
        "portraitvideoassetmodel",
        ["user_id", "actor_id", "is_current"],
        unique=False,
    )
    op.create_index(
        "ix_portraitvideoassetmodel_superseded_at",
        "portraitvideoassetmodel",
        ["superseded_at"],
        unique=False,
    )

    op.create_index(
        "uq_portraituploadsessionmodel_one_current_per_user_actor",
        "portraituploadsessionmodel",
        ["user_id", "actor_id"],
        unique=True,
        postgresql_where=sa.text("is_current = TRUE"),
    )
    op.create_index(
        "uq_portraitvideoassetmodel_one_current_per_user_actor",
        "portraitvideoassetmodel",
        ["user_id", "actor_id"],
        unique=True,
        postgresql_where=sa.text("is_current = TRUE"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_portraitvideoassetmodel_one_current_per_user_actor",
        table_name="portraitvideoassetmodel",
    )
    op.drop_index(
        "uq_portraituploadsessionmodel_one_current_per_user_actor",
        table_name="portraituploadsessionmodel",
    )

    op.drop_index("ix_portraitvideoassetmodel_superseded_at", table_name="portraitvideoassetmodel")
    op.drop_index("ix_portraitvideoassetmodel_user_actor_is_current", table_name="portraitvideoassetmodel")
    op.drop_index("ix_portraituploadsessionmodel_superseded_at", table_name="portraituploadsessionmodel")
    op.drop_index("ix_portraituploadsessionmodel_user_actor_is_current", table_name="portraituploadsessionmodel")

    op.drop_column("portraitvideoassetmodel", "superseded_at")
    op.drop_column("portraitvideoassetmodel", "is_current")
    op.drop_column("portraituploadsessionmodel", "superseded_at")
    op.drop_column("portraituploadsessionmodel", "is_current")
