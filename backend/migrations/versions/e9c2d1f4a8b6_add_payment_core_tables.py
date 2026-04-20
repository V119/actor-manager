"""Add payment core tables

Revision ID: e9c2d1f4a8b6
Revises: d2f5a7c9b1e4
Create Date: 2026-04-20 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "e9c2d1f4a8b6"
down_revision = "d2f5a7c9b1e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "paymentopsconfigmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fee_rate_bps", sa.Integer(), nullable=False, server_default="600"),
        sa.Column("auto_accept_hours", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("dispute_protect_hours", sa.Integer(), nullable=False, server_default="168"),
        sa.Column("max_hold_hours", sa.Integer(), nullable=False, server_default="4320"),
        sa.Column("settlement_safety_buffer_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("allow_wechat", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("allow_alipay", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["updated_by_id"], ["usermodel.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paymentopsconfigmodel_updated_at", "paymentopsconfigmodel", ["updated_at"], unique=False)

    op.create_table(
        "enterprisecartitemmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enterprise_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("signing_id", sa.Integer(), nullable=True),
        sa.Column("actor_quote_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quote_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enterprise_user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signing_id"], ["enterpriseactorsigningmodel.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enterprise_user_id", "actor_id", name="uq_enterprise_cart_item_enterprise_actor"),
    )
    op.create_index("ix_enterprisecartitemmodel_status", "enterprisecartitemmodel", ["status"], unique=False)
    op.create_index("ix_enterprisecartitemmodel_created_at", "enterprisecartitemmodel", ["created_at"], unique=False)
    op.create_index("ix_enterprisecartitemmodel_updated_at", "enterprisecartitemmodel", ["updated_at"], unique=False)
    op.create_index(
        "ix_enterprisecartitemmodel_enterprise_user_status_created_at",
        "enterprisecartitemmodel",
        ["enterprise_user_id", "status", "created_at"],
        unique=False,
    )

    op.create_table(
        "enterpriseordermodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enterprise_user_id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending_payment"),
        sa.Column("currency", sa.String(), nullable=False, server_default="CNY"),
        sa.Column("actor_total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("platform_fee_rate_bps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("platform_fee_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payable_total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paid_total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refunded_total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("settlement_status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("settled_total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("auto_accept_at", sa.DateTime(), nullable=True),
        sa.Column("release_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("payment_succeeded_at", sa.DateTime(), nullable=True),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("order_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["enterprise_user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no"),
    )
    op.create_index("ix_enterpriseordermodel_order_no", "enterpriseordermodel", ["order_no"], unique=True)
    op.create_index("ix_enterpriseordermodel_status", "enterpriseordermodel", ["status"], unique=False)
    op.create_index("ix_enterpriseordermodel_settlement_status", "enterpriseordermodel", ["settlement_status"], unique=False)
    op.create_index("ix_enterpriseordermodel_auto_accept_at", "enterpriseordermodel", ["auto_accept_at"], unique=False)
    op.create_index("ix_enterpriseordermodel_release_at", "enterpriseordermodel", ["release_at"], unique=False)
    op.create_index("ix_enterpriseordermodel_payment_succeeded_at", "enterpriseordermodel", ["payment_succeeded_at"], unique=False)
    op.create_index("ix_enterpriseordermodel_settled_at", "enterpriseordermodel", ["settled_at"], unique=False)
    op.create_index("ix_enterpriseordermodel_closed_at", "enterpriseordermodel", ["closed_at"], unique=False)
    op.create_index("ix_enterpriseordermodel_created_at", "enterpriseordermodel", ["created_at"], unique=False)
    op.create_index("ix_enterpriseordermodel_updated_at", "enterpriseordermodel", ["updated_at"], unique=False)
    op.create_index(
        "ix_enterpriseordermodel_enterprise_user_status_created_at",
        "enterpriseordermodel",
        ["enterprise_user_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_eorder_ent_settle_status_created_at",
        "enterpriseordermodel",
        ["enterprise_user_id", "settlement_status", "created_at"],
        unique=False,
    )

    op.create_table(
        "enterpriseorderactoritemmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("enterprise_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("cart_item_id", sa.Integer(), nullable=True),
        sa.Column("actor_quote_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("platform_fee_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("line_total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("settled_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refunded_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("item_status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("actor_receivable_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actor_release_at", sa.DateTime(), nullable=True),
        sa.Column("quote_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["enterpriseordermodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enterprise_user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"]),
        sa.ForeignKeyConstraint(["cart_item_id"], ["enterprisecartitemmodel.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "actor_id", name="uq_order_actor_item"),
    )
    op.create_index("ix_enterpriseorderactoritemmodel_item_status", "enterpriseorderactoritemmodel", ["item_status"], unique=False)
    op.create_index("ix_enterpriseorderactoritemmodel_actor_release_at", "enterpriseorderactoritemmodel", ["actor_release_at"], unique=False)
    op.create_index("ix_enterpriseorderactoritemmodel_created_at", "enterpriseorderactoritemmodel", ["created_at"], unique=False)
    op.create_index("ix_enterpriseorderactoritemmodel_updated_at", "enterpriseorderactoritemmodel", ["updated_at"], unique=False)
    op.create_index(
        "ix_enterpriseorderactoritemmodel_actor_item_status_created_at",
        "enterpriseorderactoritemmodel",
        ["actor_id", "item_status", "created_at"],
        unique=False,
    )

    op.create_table(
        "paymenttransactionmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enterprise_user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("out_trade_no", sa.String(), nullable=False),
        sa.Column("channel_trade_no", sa.String(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="initiated"),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notify_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["enterprise_user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["enterpriseordermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("out_trade_no"),
    )
    op.create_index("ix_paymenttransactionmodel_channel", "paymenttransactionmodel", ["channel"], unique=False)
    op.create_index("ix_paymenttransactionmodel_out_trade_no", "paymenttransactionmodel", ["out_trade_no"], unique=True)
    op.create_index("ix_paymenttransactionmodel_channel_trade_no", "paymenttransactionmodel", ["channel_trade_no"], unique=False)
    op.create_index("ix_paymenttransactionmodel_status", "paymenttransactionmodel", ["status"], unique=False)
    op.create_index("ix_paymenttransactionmodel_paid_at", "paymenttransactionmodel", ["paid_at"], unique=False)
    op.create_index("ix_paymenttransactionmodel_created_at", "paymenttransactionmodel", ["created_at"], unique=False)
    op.create_index("ix_paymenttransactionmodel_updated_at", "paymenttransactionmodel", ["updated_at"], unique=False)
    op.create_index(
        "ix_paymenttransactionmodel_order_status_created_at",
        "paymenttransactionmodel",
        ["order_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_paymenttransactionmodel_enterprise_user_channel_created_at",
        "paymenttransactionmodel",
        ["enterprise_user_id", "channel", "created_at"],
        unique=False,
    )

    op.create_table(
        "settlementrecordmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("actor_item_id", sa.Integer(), nullable=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(), nullable=False, server_default="internal"),
        sa.Column("out_settle_no", sa.String(), nullable=False),
        sa.Column("channel_settle_no", sa.String(), nullable=True),
        sa.Column("settle_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("platform_fee_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["enterpriseordermodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_item_id"], ["enterpriseorderactoritemmodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("out_settle_no"),
    )
    op.create_index("ix_settlementrecordmodel_channel", "settlementrecordmodel", ["channel"], unique=False)
    op.create_index("ix_settlementrecordmodel_out_settle_no", "settlementrecordmodel", ["out_settle_no"], unique=True)
    op.create_index("ix_settlementrecordmodel_channel_settle_no", "settlementrecordmodel", ["channel_settle_no"], unique=False)
    op.create_index("ix_settlementrecordmodel_status", "settlementrecordmodel", ["status"], unique=False)
    op.create_index("ix_settlementrecordmodel_requested_at", "settlementrecordmodel", ["requested_at"], unique=False)
    op.create_index("ix_settlementrecordmodel_settled_at", "settlementrecordmodel", ["settled_at"], unique=False)
    op.create_index("ix_settlementrecordmodel_created_at", "settlementrecordmodel", ["created_at"], unique=False)
    op.create_index("ix_settlementrecordmodel_updated_at", "settlementrecordmodel", ["updated_at"], unique=False)
    op.create_index(
        "ix_settlementrecordmodel_order_status_created_at",
        "settlementrecordmodel",
        ["order_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_settlementrecordmodel_actor_status_created_at",
        "settlementrecordmodel",
        ["actor_id", "status", "created_at"],
        unique=False,
    )

    op.create_table(
        "refundrecordmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enterprise_user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("actor_item_id", sa.Integer(), nullable=True),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("out_refund_no", sa.String(), nullable=False),
        sa.Column("channel_refund_no", sa.String(), nullable=True),
        sa.Column("refund_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("reason", sa.String(), nullable=False, server_default=""),
        sa.Column("operator_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notify_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["enterprise_user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["enterpriseordermodel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_item_id"], ["enterpriseorderactoritemmodel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["payment_id"], ["paymenttransactionmodel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["operator_user_id"], ["usermodel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["usermodel.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("out_refund_no"),
    )
    op.create_index("ix_refundrecordmodel_channel", "refundrecordmodel", ["channel"], unique=False)
    op.create_index("ix_refundrecordmodel_out_refund_no", "refundrecordmodel", ["out_refund_no"], unique=True)
    op.create_index("ix_refundrecordmodel_channel_refund_no", "refundrecordmodel", ["channel_refund_no"], unique=False)
    op.create_index("ix_refundrecordmodel_status", "refundrecordmodel", ["status"], unique=False)
    op.create_index("ix_refundrecordmodel_reviewed_at", "refundrecordmodel", ["reviewed_at"], unique=False)
    op.create_index("ix_refundrecordmodel_created_at", "refundrecordmodel", ["created_at"], unique=False)
    op.create_index("ix_refundrecordmodel_updated_at", "refundrecordmodel", ["updated_at"], unique=False)
    op.create_index(
        "ix_refundrecordmodel_order_status_created_at",
        "refundrecordmodel",
        ["order_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_refundrecordmodel_enterprise_user_status_created_at",
        "refundrecordmodel",
        ["enterprise_user_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_refundrecordmodel_operator_user_created_at",
        "refundrecordmodel",
        ["operator_user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "paymentauditlogmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enterprise_user_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("actor_item_id", sa.Integer(), nullable=True),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("refund_id", sa.Integer(), nullable=True),
        sa.Column("settlement_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("operator_user_id", sa.Integer(), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["enterprise_user_id"], ["usermodel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["enterpriseordermodel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["actor_item_id"], ["enterpriseorderactoritemmodel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["payment_id"], ["paymenttransactionmodel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["refund_id"], ["refundrecordmodel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["settlement_id"], ["settlementrecordmodel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["operator_user_id"], ["usermodel.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paymentauditlogmodel_action", "paymentauditlogmodel", ["action"], unique=False)
    op.create_index("ix_paymentauditlogmodel_created_at", "paymentauditlogmodel", ["created_at"], unique=False)
    op.create_index(
        "ix_paymentauditlogmodel_order_created_at",
        "paymentauditlogmodel",
        ["order_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_paymentauditlogmodel_action_created_at",
        "paymentauditlogmodel",
        ["action", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_paymentauditlogmodel_operator_user_created_at",
        "paymentauditlogmodel",
        ["operator_user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_paymentauditlogmodel_operator_user_created_at", table_name="paymentauditlogmodel")
    op.drop_index("ix_paymentauditlogmodel_action_created_at", table_name="paymentauditlogmodel")
    op.drop_index("ix_paymentauditlogmodel_order_created_at", table_name="paymentauditlogmodel")
    op.drop_index("ix_paymentauditlogmodel_created_at", table_name="paymentauditlogmodel")
    op.drop_index("ix_paymentauditlogmodel_action", table_name="paymentauditlogmodel")
    op.drop_table("paymentauditlogmodel")

    op.drop_index("ix_refundrecordmodel_operator_user_created_at", table_name="refundrecordmodel")
    op.drop_index("ix_refundrecordmodel_enterprise_user_status_created_at", table_name="refundrecordmodel")
    op.drop_index("ix_refundrecordmodel_order_status_created_at", table_name="refundrecordmodel")
    op.drop_index("ix_refundrecordmodel_updated_at", table_name="refundrecordmodel")
    op.drop_index("ix_refundrecordmodel_created_at", table_name="refundrecordmodel")
    op.drop_index("ix_refundrecordmodel_reviewed_at", table_name="refundrecordmodel")
    op.drop_index("ix_refundrecordmodel_status", table_name="refundrecordmodel")
    op.drop_index("ix_refundrecordmodel_channel_refund_no", table_name="refundrecordmodel")
    op.drop_index("ix_refundrecordmodel_out_refund_no", table_name="refundrecordmodel")
    op.drop_index("ix_refundrecordmodel_channel", table_name="refundrecordmodel")
    op.drop_table("refundrecordmodel")

    op.drop_index("ix_settlementrecordmodel_actor_status_created_at", table_name="settlementrecordmodel")
    op.drop_index("ix_settlementrecordmodel_order_status_created_at", table_name="settlementrecordmodel")
    op.drop_index("ix_settlementrecordmodel_updated_at", table_name="settlementrecordmodel")
    op.drop_index("ix_settlementrecordmodel_created_at", table_name="settlementrecordmodel")
    op.drop_index("ix_settlementrecordmodel_settled_at", table_name="settlementrecordmodel")
    op.drop_index("ix_settlementrecordmodel_requested_at", table_name="settlementrecordmodel")
    op.drop_index("ix_settlementrecordmodel_status", table_name="settlementrecordmodel")
    op.drop_index("ix_settlementrecordmodel_channel_settle_no", table_name="settlementrecordmodel")
    op.drop_index("ix_settlementrecordmodel_out_settle_no", table_name="settlementrecordmodel")
    op.drop_index("ix_settlementrecordmodel_channel", table_name="settlementrecordmodel")
    op.drop_table("settlementrecordmodel")

    op.drop_index("ix_paymenttransactionmodel_enterprise_user_channel_created_at", table_name="paymenttransactionmodel")
    op.drop_index("ix_paymenttransactionmodel_order_status_created_at", table_name="paymenttransactionmodel")
    op.drop_index("ix_paymenttransactionmodel_updated_at", table_name="paymenttransactionmodel")
    op.drop_index("ix_paymenttransactionmodel_created_at", table_name="paymenttransactionmodel")
    op.drop_index("ix_paymenttransactionmodel_paid_at", table_name="paymenttransactionmodel")
    op.drop_index("ix_paymenttransactionmodel_status", table_name="paymenttransactionmodel")
    op.drop_index("ix_paymenttransactionmodel_channel_trade_no", table_name="paymenttransactionmodel")
    op.drop_index("ix_paymenttransactionmodel_out_trade_no", table_name="paymenttransactionmodel")
    op.drop_index("ix_paymenttransactionmodel_channel", table_name="paymenttransactionmodel")
    op.drop_table("paymenttransactionmodel")

    op.drop_index("ix_enterpriseorderactoritemmodel_actor_item_status_created_at", table_name="enterpriseorderactoritemmodel")
    op.drop_index("ix_enterpriseorderactoritemmodel_updated_at", table_name="enterpriseorderactoritemmodel")
    op.drop_index("ix_enterpriseorderactoritemmodel_created_at", table_name="enterpriseorderactoritemmodel")
    op.drop_index("ix_enterpriseorderactoritemmodel_actor_release_at", table_name="enterpriseorderactoritemmodel")
    op.drop_index("ix_enterpriseorderactoritemmodel_item_status", table_name="enterpriseorderactoritemmodel")
    op.drop_table("enterpriseorderactoritemmodel")

    op.drop_index("ix_eorder_ent_settle_status_created_at", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_enterprise_user_status_created_at", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_updated_at", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_created_at", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_closed_at", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_settled_at", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_payment_succeeded_at", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_release_at", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_auto_accept_at", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_settlement_status", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_status", table_name="enterpriseordermodel")
    op.drop_index("ix_enterpriseordermodel_order_no", table_name="enterpriseordermodel")
    op.drop_table("enterpriseordermodel")

    op.drop_index("ix_enterprisecartitemmodel_enterprise_user_status_created_at", table_name="enterprisecartitemmodel")
    op.drop_index("ix_enterprisecartitemmodel_updated_at", table_name="enterprisecartitemmodel")
    op.drop_index("ix_enterprisecartitemmodel_created_at", table_name="enterprisecartitemmodel")
    op.drop_index("ix_enterprisecartitemmodel_status", table_name="enterprisecartitemmodel")
    op.drop_table("enterprisecartitemmodel")

    op.drop_index("ix_paymentopsconfigmodel_updated_at", table_name="paymentopsconfigmodel")
    op.drop_table("paymentopsconfigmodel")
