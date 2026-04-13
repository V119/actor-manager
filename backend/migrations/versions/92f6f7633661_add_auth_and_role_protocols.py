"""Add auth and role-based protocol fields

Revision ID: 92f6f7633661
Revises: 6f3144afe3bc
Create Date: 2026-04-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92f6f7633661'
down_revision = '6f3144afe3bc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'usermodel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )

    op.create_table(
        'sessionmodel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['usermodel.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )

    op.create_index('ix_sessionmodel_token', 'sessionmodel', ['token'], unique=True)

    op.alter_column('protocolmodel', 'actor_id', existing_type=sa.Integer(), nullable=True)
    op.add_column('protocolmodel', sa.Column('enterprise_user_id', sa.Integer(), nullable=True))
    op.add_column('protocolmodel', sa.Column('target_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_protocolmodel_enterprise_user',
        'protocolmodel',
        'usermodel',
        ['enterprise_user_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_protocolmodel_target_user',
        'protocolmodel',
        'usermodel',
        ['target_user_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_protocolmodel_target_user', 'protocolmodel', type_='foreignkey')
    op.drop_constraint('fk_protocolmodel_enterprise_user', 'protocolmodel', type_='foreignkey')
    op.drop_column('protocolmodel', 'target_user_id')
    op.drop_column('protocolmodel', 'enterprise_user_id')
    op.alter_column('protocolmodel', 'actor_id', existing_type=sa.Integer(), nullable=False)

    op.drop_index('ix_sessionmodel_token', table_name='sessionmodel')
    op.drop_table('sessionmodel')
    op.drop_table('usermodel')
