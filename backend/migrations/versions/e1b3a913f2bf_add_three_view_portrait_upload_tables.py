"""Add three-view portrait upload tables

Revision ID: e1b3a913f2bf
Revises: 92f6f7633661
Create Date: 2026-04-12 17:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e1b3a913f2bf"
down_revision = "92f6f7633661"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portraituploadsessionmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_key", sa.String(), nullable=False),
        sa.Column("composite_bucket", sa.String(), nullable=False),
        sa.Column("composite_object_key", sa.String(), nullable=False),
        sa.Column("composite_image_url", sa.String(), nullable=False),
        sa.Column("composite_width", sa.Integer(), nullable=False),
        sa.Column("composite_height", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_key"),
    )
    op.create_index(
        "ix_portraituploadsessionmodel_actor_user_created_at",
        "portraituploadsessionmodel",
        ["actor_id", "user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraituploadsessionmodel_created_at",
        "portraituploadsessionmodel",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraituploadsessionmodel_session_key",
        "portraituploadsessionmodel",
        ["session_key"],
        unique=True,
    )

    op.create_table(
        "portraituploadassetmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("view_angle", sa.String(), nullable=False),
        sa.Column("bucket_name", sa.String(), nullable=False),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("source_filename", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("expected_ratio", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["portraituploadsessionmodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_portraituploadassetmodel_actor_user_created_at",
        "portraituploadassetmodel",
        ["actor_id", "user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraituploadassetmodel_created_at",
        "portraituploadassetmodel",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraituploadassetmodel_session_view_angle",
        "portraituploadassetmodel",
        ["session_id", "view_angle"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_portraituploadassetmodel_session_view_angle", table_name="portraituploadassetmodel")
    op.drop_index("ix_portraituploadassetmodel_created_at", table_name="portraituploadassetmodel")
    op.drop_index("ix_portraituploadassetmodel_actor_user_created_at", table_name="portraituploadassetmodel")
    op.drop_table("portraituploadassetmodel")

    op.drop_index("ix_portraituploadsessionmodel_session_key", table_name="portraituploadsessionmodel")
    op.drop_index("ix_portraituploadsessionmodel_created_at", table_name="portraituploadsessionmodel")
    op.drop_index("ix_portraituploadsessionmodel_actor_user_created_at", table_name="portraituploadsessionmodel")
    op.drop_table("portraituploadsessionmodel")
