"""Add enterprise actor signings table

Revision ID: d2f5a7c9b1e4
Revises: c9f1a4d2e6b8
Create Date: 2026-04-17 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2f5a7c9b1e4"
down_revision = "c9f1a4d2e6b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "enterpriseactorsigningmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enterprise_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("signed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enterprise_user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enterprise_user_id", "actor_id", name="uq_enterprise_actor_signing"),
    )
    op.create_index(
        "ix_enterpriseactorsigningmodel_signed_at",
        "enterpriseactorsigningmodel",
        ["signed_at"],
        unique=False,
    )
    op.create_index(
        "ix_enterpriseactorsigningmodel_enterprise_user_id_signed_at",
        "enterpriseactorsigningmodel",
        ["enterprise_user_id", "signed_at"],
        unique=False,
    )
    op.create_index(
        "ix_enterpriseactorsigningmodel_actor_id_signed_at",
        "enterpriseactorsigningmodel",
        ["actor_id", "signed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_enterpriseactorsigningmodel_actor_id_signed_at",
        table_name="enterpriseactorsigningmodel",
    )
    op.drop_index(
        "ix_enterpriseactorsigningmodel_enterprise_user_id_signed_at",
        table_name="enterpriseactorsigningmodel",
    )
    op.drop_index(
        "ix_enterpriseactorsigningmodel_signed_at",
        table_name="enterpriseactorsigningmodel",
    )
    op.drop_table("enterpriseactorsigningmodel")
