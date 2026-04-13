"""Initial migration

Revision ID: 6f3144afe3bc
Revises:
Create Date: 2025-02-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6f3144afe3bc'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Actor Table
    op.create_table(
        'actormodel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('external_id', sa.String(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )

    # Portrait Table
    op.create_table(
        'portraitmodel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('portrait_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['actormodel.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Style Table
    op.create_table(
        'stylemodel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('preview_url', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Generated Result Table
    op.create_table(
        'generatedresultmodel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('style_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['actormodel.id'], ),
        sa.ForeignKeyConstraint(['style_id'], ['stylemodel.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Protocol Table
    op.create_table(
        'protocolmodel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('signed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['actor_id'], ['actormodel.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('protocolmodel')
    op.drop_table('generatedresultmodel')
    op.drop_table('stylemodel')
    op.drop_table('portraitmodel')
    op.drop_table('actormodel')
