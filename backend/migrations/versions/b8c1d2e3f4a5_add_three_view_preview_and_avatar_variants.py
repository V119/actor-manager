"""Add three-view preview and avatar variant fields

Revision ID: b8c1d2e3f4a5
Revises: a5f3b2c9d8e1
Create Date: 2026-04-21 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "b8c1d2e3f4a5"
down_revision = "a5f3b2c9d8e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "portraituploadassetmodel",
        sa.Column("preview_bucket_name", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadassetmodel",
        sa.Column("preview_object_key", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadassetmodel",
        sa.Column("preview_image_url", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadassetmodel",
        sa.Column("preview_mime_type", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadassetmodel",
        sa.Column("preview_width", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "portraituploadassetmodel",
        sa.Column("preview_height", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "portraituploadassetmodel",
        sa.Column("preview_file_size", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "portraituploadassetmodel",
        sa.Column("variant_map", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index(
        "ix_portraituploadassetmodel_preview_object_key",
        "portraituploadassetmodel",
        ["preview_object_key"],
        unique=False,
    )

    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("composite_preview_bucket", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("composite_preview_object_key", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("composite_preview_image_url", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("composite_file_size", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("composite_preview_file_size", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("composite_variant_map", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("avatar_bucket_name", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("avatar_object_key", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("avatar_image_url", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("avatar_mime_type", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("avatar_width", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("avatar_height", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("avatar_file_size", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "portraituploadsessionmodel",
        sa.Column("avatar_variant_map", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index(
        "ix_portraituploadsessionmodel_composite_preview_object_key",
        "portraituploadsessionmodel",
        ["composite_preview_object_key"],
        unique=False,
    )
    op.create_index(
        "ix_portraituploadsessionmodel_avatar_object_key",
        "portraituploadsessionmodel",
        ["avatar_object_key"],
        unique=False,
    )

    op.execute(
        """
        UPDATE portraituploadassetmodel
        SET preview_bucket_name = bucket_name,
            preview_object_key = object_key,
            preview_image_url = image_url,
            preview_mime_type = mime_type,
            preview_width = width,
            preview_height = height,
            preview_file_size = file_size
        """
    )
    op.execute(
        """
        UPDATE portraituploadsessionmodel
        SET composite_preview_bucket = composite_bucket,
            composite_preview_object_key = composite_object_key,
            composite_preview_image_url = composite_image_url,
            composite_variant_map = '{}'::jsonb
        """
    )

    op.execute(
        """
        ALTER TABLE portraituploadassetmodel
        ALTER COLUMN preview_bucket_name DROP DEFAULT,
        ALTER COLUMN preview_object_key DROP DEFAULT,
        ALTER COLUMN preview_image_url DROP DEFAULT,
        ALTER COLUMN preview_mime_type DROP DEFAULT,
        ALTER COLUMN preview_width DROP DEFAULT,
        ALTER COLUMN preview_height DROP DEFAULT,
        ALTER COLUMN preview_file_size DROP DEFAULT,
        ALTER COLUMN variant_map DROP DEFAULT
        """
    )
    op.execute(
        """
        ALTER TABLE portraituploadsessionmodel
        ALTER COLUMN composite_preview_bucket DROP DEFAULT,
        ALTER COLUMN composite_preview_object_key DROP DEFAULT,
        ALTER COLUMN composite_preview_image_url DROP DEFAULT,
        ALTER COLUMN composite_file_size DROP DEFAULT,
        ALTER COLUMN composite_preview_file_size DROP DEFAULT,
        ALTER COLUMN composite_variant_map DROP DEFAULT,
        ALTER COLUMN avatar_bucket_name DROP DEFAULT,
        ALTER COLUMN avatar_object_key DROP DEFAULT,
        ALTER COLUMN avatar_image_url DROP DEFAULT,
        ALTER COLUMN avatar_mime_type DROP DEFAULT,
        ALTER COLUMN avatar_width DROP DEFAULT,
        ALTER COLUMN avatar_height DROP DEFAULT,
        ALTER COLUMN avatar_file_size DROP DEFAULT,
        ALTER COLUMN avatar_variant_map DROP DEFAULT
        """
    )


def downgrade() -> None:
    op.drop_index("ix_portraituploadsessionmodel_avatar_object_key", table_name="portraituploadsessionmodel")
    op.drop_index("ix_portraituploadsessionmodel_composite_preview_object_key", table_name="portraituploadsessionmodel")

    op.drop_column("portraituploadsessionmodel", "avatar_variant_map")
    op.drop_column("portraituploadsessionmodel", "avatar_file_size")
    op.drop_column("portraituploadsessionmodel", "avatar_height")
    op.drop_column("portraituploadsessionmodel", "avatar_width")
    op.drop_column("portraituploadsessionmodel", "avatar_mime_type")
    op.drop_column("portraituploadsessionmodel", "avatar_image_url")
    op.drop_column("portraituploadsessionmodel", "avatar_object_key")
    op.drop_column("portraituploadsessionmodel", "avatar_bucket_name")
    op.drop_column("portraituploadsessionmodel", "composite_variant_map")
    op.drop_column("portraituploadsessionmodel", "composite_preview_file_size")
    op.drop_column("portraituploadsessionmodel", "composite_file_size")
    op.drop_column("portraituploadsessionmodel", "composite_preview_image_url")
    op.drop_column("portraituploadsessionmodel", "composite_preview_object_key")
    op.drop_column("portraituploadsessionmodel", "composite_preview_bucket")

    op.drop_index("ix_portraituploadassetmodel_preview_object_key", table_name="portraituploadassetmodel")
    op.drop_column("portraituploadassetmodel", "variant_map")
    op.drop_column("portraituploadassetmodel", "preview_file_size")
    op.drop_column("portraituploadassetmodel", "preview_height")
    op.drop_column("portraituploadassetmodel", "preview_width")
    op.drop_column("portraituploadassetmodel", "preview_mime_type")
    op.drop_column("portraituploadassetmodel", "preview_image_url")
    op.drop_column("portraituploadassetmodel", "preview_object_key")
    op.drop_column("portraituploadassetmodel", "preview_bucket_name")
