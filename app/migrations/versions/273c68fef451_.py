"""change notifications enum to uppercase

Revision ID: 273c68fef451
Revises: 4418fe7ee9d0
Create Date: 2020-06-26 09:09:53.035804

"""
from alembic import op
import sqlalchemy as sa




# revision identifiers, used by Alembic.
revision = '273c68fef451'
down_revision = '4418fe7ee9d0'
branch_labels = None
depends_on = None


def upgrade():
    status_enum = sa.Enum(
        'UNKNOWN', # the state of the message is not known
        name='notification_status',
        )

    transport_enum = sa.Enum(
        'SMS',
        name='notification_transport',
       )

    op.alter_column('notification', 'status', type_=status_enum)
    op.alter_column('notification', 'transport', type_=transport_enum)
    pass


def downgrade():

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
    op.alter_column('notification', 'status', type_=status_enum)
    op.alter_column('notification', 'transport', type_=transport_enum)
    pass
