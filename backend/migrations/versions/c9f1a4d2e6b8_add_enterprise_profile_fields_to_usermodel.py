"""Add enterprise profile fields to usermodel

Revision ID: c9f1a4d2e6b8
Revises: b4c6d8e2f1a0
Create Date: 2026-04-17 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c9f1a4d2e6b8"
down_revision = "b4c6d8e2f1a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usermodel",
        sa.Column("company_credit_code", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "usermodel",
        sa.Column("company_registered_address", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("usermodel", "company_registered_address")
    op.drop_column("usermodel", "company_credit_code")
