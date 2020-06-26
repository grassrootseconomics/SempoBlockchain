"""Tests the database logging of notifications sent by system
"""

# standard imports
import pytest

# platform imports
from server import db
from share.models.notification import Notification
from share.notification.enum import NotificationTransportEnum
from share.notification.enum import NotificationStatusEnum


def test_notification(test_client, init_database):
    n = Notification(NotificationTransportEnum.SMS, '+25413243546', 'everything looks bad if you remember it')
    db.session.add(n)
    db.session.commit()

    n1 = Notification.query.get(1)
    assert(n1.transport == NotificationTransportEnum.SMS)
    assert(n1.recipient == '+25413243546')
    assert(n1.content == 'everything looks bad if you remember it')
    assert(n1.status == NotificationStatusEnum.UNKNOWN)
