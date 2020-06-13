""" Adds ussd menu info title configs

Revision ID: 805c389c775b
Revises: e140854b62d2
Create Date: 2020-06-10 22:03:20.586464

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '805c389c775b'
down_revision = 'e140854b62d2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('ussd_menu_info_title_configs', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'ussd_menu_info_title_configs')
    # ### end Alembic commands ###