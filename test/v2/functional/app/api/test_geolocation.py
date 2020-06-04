# standard imports
import json
import urllib
import logging

# third party imports
import pytest

# platform imports
import config
from server import db
from helpers.factories import UserFactory
from server.utils.auth import get_complete_auth_token
from share.models.location import Location
from share.location.enum import LocationExternalSourceEnum

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
    """
    GIVEN coordinates and a name
    WHEN storing this to the legacy fields for location in db
    THEN they are retrievable through the legacy location http api call
    """

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
    """
    GIVEN a hierarchical location relation
    WHEN querying the location through the http api
    THEN a matching name and/or path returns the location
    """

    # test leaf name matching
    common_name_urlencoded = urllib.parse.quote(new_locations['leaf'].common_name.encode('utf-8'))
    response = test_client.get(
            '/api/v2/geolocation/{}/'.format(common_name_urlencoded),
             headers=dict(
                Accept='application/json',
                ),
            )
    assert response.status_code == 200
    assert response.json['locations'][0]['path'] == '{}, {}, {}'.format(new_locations['leaf'].common_name, new_locations['node'].common_name, new_locations['top'].common_name)

    # test path matching
    path_urlencoded = '{}/{}'.format(
        urllib.parse.quote(new_locations['leaf'].common_name.encode('utf-8')),
        urllib.parse.quote(new_locations['node'].common_name.encode('utf-8')),
            )
    response = test_client.get(
            '/api/v2/geolocation/{}/'.format(path_urlencoded),
             headers=dict(
                Accept='application/json',
                ),
            )
    assert response.status_code == 200

    # test that path mismatch is caught
    path_urlencoded = '{}/foo'.format(
        urllib.parse.quote(new_locations['leaf'].common_name.encode('utf-8')),
            )
    response = test_client.get(
            '/api/v2/geolocation/{}/'.format(path_urlencoded),
             headers=dict(
                Accept='application/json',
                ),
            )
    assert response.status_code == 404 



def test_get_existing_location_by_external_id(
        test_client,
        init_database,
        new_locations,
        ):
        """
        GIVEN a hierarchical location relation with external metadata
        WHEN querying custom location data lookup endpoint in http api
        THEN the entry matching the metadata key/value pair is returned
        """
        ext_data_osm = {
                'place_id': 42,
                'osm_id': 666,
                }
        new_locations['leaf'].add_external_data(LocationExternalSourceEnum.OSM.value, ext_data_osm)
        db.session.commit()

        response = test_client.get(
                '/api/v2/geolocation/{}/{}/'.format(LocationExternalSourceEnum.OSM.name, ext_data_osm['place_id']),
                headers=dict(
                    Accept='application/json',
                    ),
                )
        assert response.status_code == 200

        response = test_client.get(
                '/api/v2/geolocation/{}/{}/'.format(LocationExternalSourceEnum.OSM.name, 43),
                headers=dict(
                    Accept='application/json',
                    ),
                )
        assert response.status_code == 404

        response = test_client.get(
                '/api/v2/geolocation/FOO/22/',
                headers=dict(
                    Accept='application/json',
                    ),
                )
        assert response.status_code == 400


def test_add_location_by_name( test_client,
    init_database,
    ):
    """
    GIVEN location data with and without external data
    WHEN added to the database through http api
    THEN the object is retrievable through db
    """

    parent = {
        'common_name': 'Catemaco',
        'latitude': 18.4179638,
        'longitude': -95.1098723,
        }
    
    response = test_client.post(
        '/api/v2/geolocation/',
        headers=dict(
            Accept='application/json',
            ),
        data=json.dumps(parent),
        content_type='application/json',
        follow_redirects=True,
        )

    assert response.status_code == 201
    parent_id = response.json['data']['location']['id']
    child = {
        'common_name': 'Monkey Island',
        'latitude': 18.4119194,
        'longitude': -95.0960522,
        'parent_id': parent_id,
        LocationExternalSourceEnum.OSM.name: {
            'osm_type': 'node',
            'osm_id': 666,
            'class': 'place',
        },
        }
    response = test_client.post(
        '/api/v2/geolocation/',
        headers=dict(
            Accept='application/json',
            ),
        data=json.dumps(child),
        content_type='application/json',
        follow_redirects=True,
        )

    assert response.status_code == 201

    child_id = response.json['data']['location']['id']
    child_location = Location.query.get(child_id)

    parent_location = child_location.parent
    assert parent_location.id == parent_id

    assert child_location.is_same_external_data(LocationExternalSourceEnum.OSM, child[LocationExternalSourceEnum.OSM.name])


def test_add_location_fail_duplicate(
        test_client,
        init_database
        ):

    parent = {
        'common_name': 'Catemaco',
        'latitude': 18.4179638,
        'longitude': -95.1098723,
        }
 
    response = test_client.post(
        '/api/v2/geolocation/',
        headers=dict(
            Accept='application/json',
            ),
        data=json.dumps(parent),
        content_type='application/json',
        follow_redirects=True,
        )

    parent_id = response.json['data']['location']['id']

    child = {
        'common_name': 'Monkey Island',
        'latitude': 18.4119194,
        'longitude': -95.0960522,
        'parent_id': parent_id,
        }
    child_ext = {
            'osm_type': 'node',
            'osm_id': 666,
            'class': 'place',
        }

    response = test_client.post(
        '/api/v2/geolocation/',
        headers=dict(
            Accept='application/json',
            ),
        data=json.dumps(child),
        content_type='application/json',
        follow_redirects=True,
        )

    assert response.status_code == 201

    response = test_client.post(
        '/api/v2/geolocation/',
        headers=dict(
            Accept='application/json',
            ),
        data=json.dumps(child),
        content_type='application/json',
        follow_redirects=True,
        )

    assert response.status_code == 500

    child['common_name'] = 'Monkey Island 2'
    child[LocationExternalSourceEnum.OSM.name] = child_ext

    response = test_client.post(
        '/api/v2/geolocation/',
        headers=dict(
            Accept='application/json',
            ),
        data=json.dumps(child),
        content_type='application/json',
        follow_redirects=True,
        )

    assert response.status_code == 500


