"""Add lifecycle fields for generated style results

Revision ID: f1c6d4b8a9e2
Revises: e7d1b2f0c4a9
Create Date: 2026-04-12 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1c6d4b8a9e2"
down_revision = "e7d1b2f0c4a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generatedresultmodel",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("usermodel.id", ondelete="CASCADE"), nullable=True),
    )
    op.add_column(
        "generatedresultmodel",
        sa.Column("lifecycle_state", sa.String(), nullable=True, server_default="draft"),
    )
    op.add_column(
        "generatedresultmodel",
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "generatedresultmodel",
        sa.Column("published_at", sa.DateTime(), nullable=True),
    )

    # Backfill owner user from actor external_id pattern: USER-<id>.
    op.execute(
        """
        UPDATE generatedresultmodel g
        SET user_id = CAST(substring(a.external_id from 'USER-([0-9]+)') AS INTEGER)
        FROM actormodel a
        WHERE g.actor_id = a.id
          AND a.external_id LIKE 'USER-%'
        """
    )

    # Historical generated results are treated as published baseline.
    op.execute("UPDATE generatedresultmodel SET lifecycle_state = 'published', published_at = created_at")

    op.alter_column(
        "generatedresultmodel",
        "lifecycle_state",
        existing_type=sa.String(),
        nullable=False,
        server_default="draft",
    )

    op.create_index(
        "ix_generatedresultmodel_user_lifecycle_created_at",
        "generatedresultmodel",
        ["user_id", "lifecycle_state", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_generatedresultmodel_lifecycle_state",
        "generatedresultmodel",
        ["lifecycle_state"],
        unique=False,
    )
    op.create_index(
        "ix_generatedresultmodel_published_at",
        "generatedresultmodel",
        ["published_at"],
        unique=False,
    )
    op.create_index(
        "ix_generatedresultmodel_superseded_at",
        "generatedresultmodel",
        ["superseded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_generatedresultmodel_superseded_at", table_name="generatedresultmodel")
    op.drop_index("ix_generatedresultmodel_published_at", table_name="generatedresultmodel")
    op.drop_index("ix_generatedresultmodel_lifecycle_state", table_name="generatedresultmodel")
    op.drop_index("ix_generatedresultmodel_user_lifecycle_created_at", table_name="generatedresultmodel")

    op.drop_column("generatedresultmodel", "published_at")
    op.drop_column("generatedresultmodel", "superseded_at")
    op.drop_column("generatedresultmodel", "lifecycle_state")
    op.drop_column("generatedresultmodel", "user_id")
