"""Add notifications logging to database

Revision ID: 4418fe7ee9d0
Revises: 805c389c775b
Create Date: 2020-06-24 15:06:15.809828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4418fe7ee9d0'
down_revision = '805c389c775b'
branch_labels = None
depends_on = None

status_enum = sa.Enum(
    'unsent', # message has not been sent, and unknown whether will be sent or not
    'queue', # message is waiting to be sent or resent,
    'sent', # message has been sent,
    'failed', # message has failed to sent and will not be retried
    'bounced', # message was sent but delivery agent could not deliver
    'confirmed', # message was sent and delivery was confirmed
    name='notification_status',
    )

transport_enum = sa.Enum(
    'email',
    'sms',
    name='notification_transport',
   )

def upgrade():
    op.create_table('notification',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('transport', transport_enum, nullable=False),
            sa.Column('status', status_enum, nullable=False),
            sa.Column('status_code', sa.String(), nullable=True),
            sa.Column('status_serial', sa.Integer(), nullable=False),
            sa.Column('recipient', sa.String(), nullable=False),
            sa.Column('created', sa.DateTime(), nullable=False),
            sa.Column('updated', sa.DateTime(), nullable=False),
            sa.Column('content', sa.String(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('notification_recipient_transport_idx', 'notification', ['transport', 'recipient'], schema=None, unique=False)
    pass


def downgrade():
    op.drop_index('notification_recipient_transport_idx')
    op.drop_table('notification')
    status_enum.drop(op.get_bind(), checkfirst=False)
    transport_enum.drop(op.get_bind(), checkfirst=False)
    pass
