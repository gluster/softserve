"""Add a new column deleted_at in table vm

Revision ID: ac40d51a4114
Revises: 45b003a9a66f
Create Date: 2018-03-20 15:23:15.806539

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ac40d51a4114'
down_revision = '45b003a9a66f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('vm', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('vm', 'deleted_at')
