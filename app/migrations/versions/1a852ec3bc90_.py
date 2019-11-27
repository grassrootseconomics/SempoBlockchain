"""empty message

Revision ID: 1a852ec3bc90
Revises: 8d672062eb10
Create Date: 2019-10-23 12:26:53.725999

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a852ec3bc90'
down_revision = '8d672062eb10'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('default_transfer_account_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'transfer_account', ['default_transfer_account_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'default_transfer_account_id')
    # ### end Alembic commands ###