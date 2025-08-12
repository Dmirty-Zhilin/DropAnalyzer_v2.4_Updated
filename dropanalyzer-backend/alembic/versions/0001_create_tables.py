
"""create domains and reports tables

Revision ID: 0001_create_tables
Revises: 
Create Date: 2025-08-10T08:40:06.670146
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
# revision identifiers, used by Alembic.
revision = '0001_create_tables'
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    op.create_table(
        'domains',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('long_live', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_domains_name'), 'domains', ['name'], unique=False)
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('domain_id', sa.Integer(), sa.ForeignKey('domains.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
def downgrade():
    op.drop_table('reports')
    op.drop_index(op.f('ix_domains_name'), table_name='domains')
    op.drop_table('domains')
