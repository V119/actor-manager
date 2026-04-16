"""Add enterprise agreement tables

Revision ID: a9d4e7f1c2b3
Revises: f2a7c9d4e6b1
Create Date: 2026-04-17 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a9d4e7f1c2b3"
down_revision = "f2a7c9d4e6b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "enterpriseagreementtemplateconfigmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_document_name", sa.String(), nullable=False, server_default=""),
        sa.Column("party_a_company_name", sa.String(), nullable=False, server_default=""),
        sa.Column("party_a_credit_code", sa.String(), nullable=False, server_default=""),
        sa.Column("party_a_registered_address", sa.Text(), nullable=False, server_default=""),
        sa.Column("authorization_start_date", sa.Date(), nullable=True),
        sa.Column("authorization_end_date", sa.Date(), nullable=True),
        sa.Column("party_a_signature_label", sa.String(), nullable=False, server_default=""),
        sa.Column("party_a_signed_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_enterpriseagreementtemplateconfigmodel_updated_at",
        "enterpriseagreementtemplateconfigmodel",
        ["updated_at"],
        unique=False,
    )

    op.create_table(
        "enterpriseagreementmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("party_b_company_name", sa.String(), nullable=False),
        sa.Column("party_b_credit_code", sa.String(), nullable=False),
        sa.Column("party_b_registered_address", sa.Text(), nullable=False),
        sa.Column("party_b_signature_data_url", sa.Text(), nullable=False),
        sa.Column("party_b_signed_date", sa.Date(), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_enterpriseagreementmodel_template_version", "enterpriseagreementmodel", ["template_version"], unique=False)
    op.create_index("ix_enterpriseagreementmodel_status", "enterpriseagreementmodel", ["status"], unique=False)
    op.create_index("ix_enterpriseagreementmodel_signed_at", "enterpriseagreementmodel", ["signed_at"], unique=False)
    op.create_index("ix_enterpriseagreementmodel_updated_at", "enterpriseagreementmodel", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_enterpriseagreementmodel_updated_at", table_name="enterpriseagreementmodel")
    op.drop_index("ix_enterpriseagreementmodel_signed_at", table_name="enterpriseagreementmodel")
    op.drop_index("ix_enterpriseagreementmodel_status", table_name="enterpriseagreementmodel")
    op.drop_index("ix_enterpriseagreementmodel_template_version", table_name="enterpriseagreementmodel")
    op.drop_table("enterpriseagreementmodel")

    op.drop_index("ix_enterpriseagreementtemplateconfigmodel_updated_at", table_name="enterpriseagreementtemplateconfigmodel")
    op.drop_table("enterpriseagreementtemplateconfigmodel")
