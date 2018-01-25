"""empty message

Revision ID: 2cde9af1890f
Revises:
Create Date: 2018-01-22 16:44:11.305278

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2cde9af1890f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'Node_request',
        sa.Column('user_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(None, 'Node_request', 'User', ['user_id'], ['id'])
    op.drop_constraint(None, 'Vm', type_='foreignkey')
    op.drop_column('Vm', 'user_id')


def downgrade():
    op.add_column('Vm', sa.Column('user_id', sa.INTEGER(), nullable=True))
    op.create_foreign_key(None, 'Vm', 'User', ['user_id'], ['id'])
    op.drop_constraint(None, 'Node_request', type_='foreignkey')
    op.drop_column('Node_request', 'user_id')
