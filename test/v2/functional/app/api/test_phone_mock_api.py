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
    float_phone = '+25411223344'
    n = Notification(NotificationTransportEnum.SMS, authed_sempo_admin_user.phone, 'i have the best words')
    n2 = Notification(NotificationTransportEnum.SMS, float_phone, 'i am a big boy')
    n3 = Notification(NotificationTransportEnum.SMS, float_phone, 'this car is not red')

    db.session.add(n)
    db.session.add(n2)
    db.session.add(n3)
    db.session.add(authed_sempo_admin_user)
    db.session.commit()

    response = test_client.get(
            '/api/v2/sms/',
            headers=dict(
                Authorization=auth,
                Accept='application/json',
                ),
            )

    assert response.status_code == 200
    assert len(response.json) == 3

    response = test_client.get(
            '/api/v2/sms/?limit=2',
            headers=dict(
                Authorization=auth,
                Accept='application/json',
                ),
            )

    assert response.status_code == 200
    assert len(response.json) == 2

    response = test_client.get(
            '/api/v2/sms/user/{}/'.format(authed_sempo_admin_user.id),
            headers=dict(
                Authorization=auth,
                Accept='application/json',
                ),
            )

    assert response.status_code == 200
    assert len(response.json) == 1

    response = test_client.get(
            '/api/v2/sms/{}/'.format(float_phone),
            headers=dict(
                Authorization=auth,
                Accept='application/json',
                ),
            )

    assert response.status_code == 200
    assert len(response.json) == 2
