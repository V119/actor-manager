"""Add compose jobs and hot-path indexes

Revision ID: b2f4a6c1d9e7
Revises: 7c5f2efaf8c1
Create Date: 2026-04-12 19:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "b2f4a6c1d9e7"
down_revision = "7c5f2efaf8c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portraitcomposejobmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_key", sa.String(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result_session_id", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["result_session_id"], ["portraituploadsessionmodel.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_key"),
    )
    op.create_index("ix_portraitcomposejobmodel_job_key", "portraitcomposejobmodel", ["job_key"], unique=True)
    op.create_index("ix_portraitcomposejobmodel_status", "portraitcomposejobmodel", ["status"], unique=False)
    op.create_index("ix_portraitcomposejobmodel_created_at", "portraitcomposejobmodel", ["created_at"], unique=False)
    op.create_index("ix_portraitcomposejobmodel_updated_at", "portraitcomposejobmodel", ["updated_at"], unique=False)
    op.create_index(
        "ix_portraitcomposejobmodel_user_status_created_at",
        "portraitcomposejobmodel",
        ["user_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraitcomposejobmodel_status_created_at",
        "portraitcomposejobmodel",
        ["status", "created_at"],
        unique=False,
    )

    # Hot-path query indexes for large-volume user uploads.
    op.create_index(
        "ix_portraituploadsessionmodel_user_created_at",
        "portraituploadsessionmodel",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraituploadassetmodel_user_created_at",
        "portraituploadassetmodel",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraituploadassetmodel_object_key",
        "portraituploadassetmodel",
        ["object_key"],
        unique=False,
    )
    op.create_index(
        "ix_portraitvideoassetmodel_user_created_at",
        "portraitvideoassetmodel",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_portraitvideoassetmodel_object_key",
        "portraitvideoassetmodel",
        ["object_key"],
        unique=False,
    )

    # BRIN indexes for append-only time-series like access patterns.
    op.execute(
        "CREATE INDEX IF NOT EXISTS brin_portraituploadsessionmodel_created_at "
        "ON portraituploadsessionmodel USING BRIN (created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS brin_portraituploadassetmodel_created_at "
        "ON portraituploadassetmodel USING BRIN (created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS brin_portraitvideoassetmodel_created_at "
        "ON portraitvideoassetmodel USING BRIN (created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS brin_portraitvideoassetmodel_created_at")
    op.execute("DROP INDEX IF EXISTS brin_portraituploadassetmodel_created_at")
    op.execute("DROP INDEX IF EXISTS brin_portraituploadsessionmodel_created_at")

    op.drop_index("ix_portraitvideoassetmodel_object_key", table_name="portraitvideoassetmodel")
    op.drop_index("ix_portraitvideoassetmodel_user_created_at", table_name="portraitvideoassetmodel")
    op.drop_index("ix_portraituploadassetmodel_object_key", table_name="portraituploadassetmodel")
    op.drop_index("ix_portraituploadassetmodel_user_created_at", table_name="portraituploadassetmodel")
    op.drop_index("ix_portraituploadsessionmodel_user_created_at", table_name="portraituploadsessionmodel")

    op.drop_index("ix_portraitcomposejobmodel_status_created_at", table_name="portraitcomposejobmodel")
    op.drop_index("ix_portraitcomposejobmodel_user_status_created_at", table_name="portraitcomposejobmodel")
    op.drop_index("ix_portraitcomposejobmodel_updated_at", table_name="portraitcomposejobmodel")
    op.drop_index("ix_portraitcomposejobmodel_created_at", table_name="portraitcomposejobmodel")
    op.drop_index("ix_portraitcomposejobmodel_status", table_name="portraitcomposejobmodel")
    op.drop_index("ix_portraitcomposejobmodel_job_key", table_name="portraitcomposejobmodel")
    op.drop_table("portraitcomposejobmodel")
