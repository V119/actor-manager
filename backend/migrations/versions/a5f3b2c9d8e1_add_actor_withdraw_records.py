"""Add actor withdraw records

Revision ID: a5f3b2c9d8e1
Revises: e9c2d1f4a8b6
Create Date: 2026-04-20 23:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "a5f3b2c9d8e1"
down_revision = "e9c2d1f4a8b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "actorwithdrawrecordmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("out_withdraw_no", sa.String(), nullable=False),
        sa.Column("channel_withdraw_no", sa.String(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("account_name", sa.String(), nullable=False, server_default=""),
        sa.Column("account_no", sa.String(), nullable=False, server_default=""),
        sa.Column("account_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("remark", sa.String(), nullable=False, server_default=""),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=False, server_default=""),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("out_withdraw_no"),
    )
    op.create_index("ix_actorwithdrawrecordmodel_channel", "actorwithdrawrecordmodel", ["channel"], unique=False)
    op.create_index("ix_actorwithdrawrecordmodel_out_withdraw_no", "actorwithdrawrecordmodel", ["out_withdraw_no"], unique=True)
    op.create_index(
        "ix_actorwithdrawrecordmodel_channel_withdraw_no",
        "actorwithdrawrecordmodel",
        ["channel_withdraw_no"],
        unique=False,
    )
    op.create_index("ix_actorwithdrawrecordmodel_status", "actorwithdrawrecordmodel", ["status"], unique=False)
    op.create_index("ix_actorwithdrawrecordmodel_requested_at", "actorwithdrawrecordmodel", ["requested_at"], unique=False)
    op.create_index("ix_actorwithdrawrecordmodel_processed_at", "actorwithdrawrecordmodel", ["processed_at"], unique=False)
    op.create_index("ix_actorwithdrawrecordmodel_created_at", "actorwithdrawrecordmodel", ["created_at"], unique=False)
    op.create_index("ix_actorwithdrawrecordmodel_updated_at", "actorwithdrawrecordmodel", ["updated_at"], unique=False)
    op.create_index(
        "ix_awithdraw_actor_status_created_at",
        "actorwithdrawrecordmodel",
        ["actor_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_awithdraw_actor_user_created_at",
        "actorwithdrawrecordmodel",
        ["actor_user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_awithdraw_actor_user_created_at", table_name="actorwithdrawrecordmodel")
    op.drop_index("ix_awithdraw_actor_status_created_at", table_name="actorwithdrawrecordmodel")
    op.drop_index("ix_actorwithdrawrecordmodel_updated_at", table_name="actorwithdrawrecordmodel")
    op.drop_index("ix_actorwithdrawrecordmodel_created_at", table_name="actorwithdrawrecordmodel")
    op.drop_index("ix_actorwithdrawrecordmodel_processed_at", table_name="actorwithdrawrecordmodel")
    op.drop_index("ix_actorwithdrawrecordmodel_requested_at", table_name="actorwithdrawrecordmodel")
    op.drop_index("ix_actorwithdrawrecordmodel_status", table_name="actorwithdrawrecordmodel")
    op.drop_index("ix_actorwithdrawrecordmodel_channel_withdraw_no", table_name="actorwithdrawrecordmodel")
    op.drop_index("ix_actorwithdrawrecordmodel_out_withdraw_no", table_name="actorwithdrawrecordmodel")
    op.drop_index("ix_actorwithdrawrecordmodel_channel", table_name="actorwithdrawrecordmodel")
    op.drop_table("actorwithdrawrecordmodel")
