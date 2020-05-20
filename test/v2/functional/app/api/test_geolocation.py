# standard imports
import json
import urllib
import logging

# third party imports
import pytest

# platform imports
import config
from helpers.factories import UserFactory
from server.utils.auth import get_complete_auth_token

logg = logging.getLogger()

@pytest.mark.parametrize('param_latitude, param_longitude, param_common_name', [
    (18.4119194, -95.0960522, 'Monkey Island Catemaco'),
    ])
def test_get_legacy_location(
        test_client,
        init_database,
        create_organisation,
        authed_sempo_admin_user,
        param_latitude,
        param_longitude,
        param_common_name):

    # create organisation
    organisation = create_organisation
    organisation.external_auth_password = config.EXTERNAL_AUTH_PASSWORD

    # create admin
    admin = authed_sempo_admin_user
    admin.set_held_role('ADMIN', 'admin')

    # create user with legacy location information
    user = UserFactory(id=42,
        lat=param_latitude,
        lng=param_longitude,
        _location=param_common_name,
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
    assert response.json['location'] == param_common_name


def test_get_existing_location_by_name(
        test_client,
        init_database,
        new_locations,
        ):

    common_name_urlencoded = urllib.parse.quote(new_locations['leaf'].common_name.encode('utf-8'))
    response = test_client.get(
            '/api/v2/geolocation/{}/'.format(common_name_urlencoded),
             headers=dict(
                Accept='application/json',
                ),
            )

    assert response.status_code == 200
    logg.debug('response json {}'.format(response.json))
    assert response.json['local'][0]['path'] == '{}, {}, {}'.format(new_locations['leaf'].common_name, new_locations['node'].common_name, new_locations['top'].common_name)


def test_add_location_by_name(
    test_client,
    init_database,
    ):

    parent = {
        'common_name': 'Catemaco',
        'latitude': 18.4179638,
        'longitude': -95.1098723,
        }
    child = {
        'common_name': 'Monkey Island',
        'latitude': 18.4119194,
        'longitude': -95.0960522,
        }
    response = test_client.post(
        '/api/v2/geolocation/',
         headers=dict(
            Accept='application/json',
            ),
         data=json.dumps(dict(
            latitude=parent['latitude'],
            longitude=parent['longitude'],
            common_name=parent['common_name'],
             )),
        content_type='application/json',
        follow_redirects=True,
        )

    assert response.status_code == 201
    logg.debug(response.json)
    parent_id = response.json['data']['location']['id']
    response = test_client.post(
        '/api/v2/geolocation/',
         headers=dict(
            Accept='application/json',
            ),
         data=json.dumps(dict(
            latitude=child['latitude'],
            longitude=child['longitude'],
            common_name=child['common_name'],
            parent_id=parent_id,
             )),
        content_type='application/json',
        follow_redirects=True,
        )

    assert response.status_code == 201
    logg.debug(response.json) 

