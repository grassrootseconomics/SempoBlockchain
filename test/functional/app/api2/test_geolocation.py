# standard imports
import json

# third party imports
import pytest

# platform imports
import config
from helpers.factories import UserFactory, TransferUsageFactory, OrganisationFactory
from server.utils.auth import get_complete_auth_token

@pytest.mark.parametrize('param_latitude, param_longitude, param_location', [
    (18.4119194, -95.0960522, 'Monkey Island Catemaco'),
    ])
def test_get_legacy_location(
        test_client,
        init_database,
        create_organisation,
        authed_sempo_admin_user,
        param_latitude,
        param_longitude,
        param_location):

    # create organisation
    organisation = create_organisation
    organisation.external_auth_password = config.EXTERNAL_AUTH_PASSWORD

    # create admin
    admin = authed_sempo_admin_user
    admin.set_held_role('ADMIN', 'admin')

    # create self signup user
    user = UserFactory(id=42,
        lat=param_latitude,
        lng=param_longitude,
        _location=param_location,
        )

    user.add_user_to_organisation(organisation, False)

    # get admin auth token
    auth = get_complete_auth_token(authed_sempo_admin_user)

    response = test_client.get(
            '/api/v2/geolocation/legacy/user/42/',
            headers=dict(
                Authorization=auth,
                Accept='application/json',
                ),
            )

    assert response.status_code == 200
    assert response.json['lat'] == param_latitude
    assert response.json['lng'] == param_longitude
    assert response.json['location'] == param_location
