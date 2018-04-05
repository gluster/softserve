"""Add a admin column to User model

Revision ID: 1948d166adb1
Revises: ac40d51a4114
Create Date: 2018-04-05 15:50:43.628791

"""
from alembic import op
import sqlalchemy as sa


revision = '1948d166adb1'
down_revision = 'ac40d51a4114'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('admin', sa.Boolean(),
                                    server_default=False, nullable=False))


def downgrade():
    op.drop_column('user', 'admin')
