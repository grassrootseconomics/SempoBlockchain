"""Add unique constraint for location path

Revision ID: e140854b62d2
Revises: 241af81119c4
Create Date: 2020-06-04 12:59:01.688443

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e140854b62d2'
down_revision = '241af81119c4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('location_path_unique_idx', 'location', ['common_name', 'parent_id'], None, True)
    pass


def downgrade():
    op.drop_index('location_path_unique_idx')
    pass
