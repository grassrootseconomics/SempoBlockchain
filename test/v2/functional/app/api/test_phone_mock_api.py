# standard imports
import pytest
import logging

# platform imports
from server.utils.auth import get_complete_auth_token

logg = logging.getLogger()

def test_sms_list(test_client, init_database, authed_sempo_admin_user):

    # create admin
    admin = authed_sempo_admin_user
    admin.set_held_role('ADMIN', 'subadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)

    response = test_client.get(
            '/api/v2/sms/',
            headers=dict(
                Authorization=auth,
                Accept='text/plain',
                ),
            )

    assert response.status_code == 200
