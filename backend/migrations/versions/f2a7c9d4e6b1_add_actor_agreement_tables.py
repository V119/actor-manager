"""Add actor agreement tables

Revision ID: f2a7c9d4e6b1
Revises: c3d8e5f7a1b2
Create Date: 2026-04-16 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f2a7c9d4e6b1"
down_revision = "c3d8e5f7a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agreementtemplateconfigmodel",
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
        "ix_agreementtemplateconfigmodel_updated_at",
        "agreementtemplateconfigmodel",
        ["updated_at"],
        unique=False,
    )

    op.create_table(
        "actoragreementmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("party_b_name", sa.String(), nullable=False),
        sa.Column("party_b_gender", sa.String(), nullable=False),
        sa.Column("party_b_identity_number", sa.String(), nullable=False),
        sa.Column("party_b_contact_address", sa.Text(), nullable=False),
        sa.Column("party_b_phone", sa.String(), nullable=False),
        sa.Column("party_b_email", sa.String(), nullable=False),
        sa.Column("party_b_signature_data_url", sa.Text(), nullable=False),
        sa.Column("party_b_signed_date", sa.Date(), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actormodel.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["usermodel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("actor_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_actoragreementmodel_template_version", "actoragreementmodel", ["template_version"], unique=False)
    op.create_index("ix_actoragreementmodel_status", "actoragreementmodel", ["status"], unique=False)
    op.create_index("ix_actoragreementmodel_signed_at", "actoragreementmodel", ["signed_at"], unique=False)
    op.create_index("ix_actoragreementmodel_updated_at", "actoragreementmodel", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_actoragreementmodel_updated_at", table_name="actoragreementmodel")
    op.drop_index("ix_actoragreementmodel_signed_at", table_name="actoragreementmodel")
    op.drop_index("ix_actoragreementmodel_status", table_name="actoragreementmodel")
    op.drop_index("ix_actoragreementmodel_template_version", table_name="actoragreementmodel")
    op.drop_table("actoragreementmodel")

    op.drop_index("ix_agreementtemplateconfigmodel_updated_at", table_name="agreementtemplateconfigmodel")
    op.drop_table("agreementtemplateconfigmodel")
