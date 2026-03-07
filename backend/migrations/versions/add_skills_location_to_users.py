"""add skills and location to users

Revision ID: a1b2c3d4e5f6
Revises: 324ffdd965a3
Create Date: 2026-03-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '324ffdd965a3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('skills', sa.ARRAY(sa.Text()), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('users', 'location')
    op.drop_column('users', 'skills')
