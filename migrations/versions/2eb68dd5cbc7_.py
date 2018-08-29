"""empty message

Revision ID: 2eb68dd5cbc7
Revises: 1948d166adb1
Create Date: 2018-08-27 16:16:36.073709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2eb68dd5cbc7'
down_revision = '1948d166adb1'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('node_request', 'pubkey')
    op.add_column('user', sa.Column('pubkey',
                                    sa.VARCHAR(length=1024),
                                    nullable=False))


def downgrade():
    op.drop_column('user', 'pubkey')
    op.add_column('node_request', sa.Column('pubkey',
                                            sa.VARCHAR(length=1024),
                                            nullable=False))
