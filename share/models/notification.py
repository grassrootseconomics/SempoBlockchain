# platform imports
from server import db
from server.models.utils import ModelBase
from share.notification.enum import NotificationStatusEnum
from share.notification.enum import NotificationTransportEnum

class Notification(ModelBase):
    __tablename__ = 'notification'

    transport = db.Column(db.Enum(NotificationTransportEnum))
    status = db.Column(db.Enum(NotificationStatusEnum))
    recipient = db.Column(db.String)
    content = db.Column(db.String)

    def __init__(self, transport, recipient, content, **kwargs):
        super(Notification, self).__init__(**kwargs)
        self.transport = transport
        self.recipient = recipient
        self.content = content
        self.status = NotificationStatusEnum.UNSENT
