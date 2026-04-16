"""Add agreement authorization date mode fields

Revision ID: b4c6d8e2f1a0
Revises: a9d4e7f1c2b3
Create Date: 2026-04-17 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b4c6d8e2f1a0"
down_revision = "a9d4e7f1c2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agreementtemplateconfigmodel",
        sa.Column("authorization_date_mode", sa.String(), nullable=False, server_default="fixed"),
    )
    op.add_column(
        "agreementtemplateconfigmodel",
        sa.Column("authorization_term_months", sa.Integer(), nullable=True),
    )

    op.add_column(
        "enterpriseagreementtemplateconfigmodel",
        sa.Column("authorization_date_mode", sa.String(), nullable=False, server_default="fixed"),
    )
    op.add_column(
        "enterpriseagreementtemplateconfigmodel",
        sa.Column("authorization_term_months", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("enterpriseagreementtemplateconfigmodel", "authorization_term_months")
    op.drop_column("enterpriseagreementtemplateconfigmodel", "authorization_date_mode")
    op.drop_column("agreementtemplateconfigmodel", "authorization_term_months")
    op.drop_column("agreementtemplateconfigmodel", "authorization_date_mode")
