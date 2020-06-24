# standard imports
import pytest
import logging

# platform imports
from server import db
from server.utils.auth import get_complete_auth_token
from share.models.notification import Notification
from share.notification.enum import NotificationTransportEnum

logg = logging.getLogger()


def test_sms_list(test_client, init_database, authed_sempo_admin_user):

    # create admin
    admin = authed_sempo_admin_user
    admin.set_held_role('ADMIN', 'subadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)
    authed_sempo_admin_user.phone = '+25413243546'
    n = Notification(NotificationTransportEnum.SMS, authed_sempo_admin_user.phone, 'i have the best words')

    db.session.add(n)
    db.session.add(authed_sempo_admin_user)
    db.session.commit()

    response = test_client.get(
            '/api/v2/sms/',
            headers=dict(
                Authorization=auth,
                Accept='text/plain',
                ),
            )

    assert response.status_code == 200
    assert len(response.json) == 1

    # TODO implement user filter
    response = test_client.get(
            '/api/v2/sms/1/',
            headers=dict(
                Authorization=auth,
                Accept='text/plain',
                ),
            )

    assert response.status_code == 200
