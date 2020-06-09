# standard imports
import json

# third-party imports
import pytest

# platform imports
import config
from server import db
from server.utils.auth import get_complete_auth_token

# test imports
from helpers.v2.factories import ExtendedUserFactory, LocationFactory


def test_get_user_location(
        test_client,
        init_database,
        create_organisation,
        authed_sempo_admin_user,
        new_locations,
        create_temporary_extended_user,
        ):
    """
    GIVEN an extended user record
    WHEN adding location to that user
    THEN the location is retrievable from the user location http api endpoint
    """

    # create organisation
    organisation = create_organisation
    organisation.external_auth_password = config.EXTERNAL_AUTH_PASSWORD

    # create admin
    admin = authed_sempo_admin_user
    admin.set_held_role('ADMIN', 'admin')

    # create user
    user = create_temporary_extended_user
    user.full_location = new_locations['leaf']
    db.session.commit()

    user.get_base_user().add_user_to_organisation(organisation, False)

    # get admin auth token
    auth = get_complete_auth_token(authed_sempo_admin_user)

    response = test_client.get(
            '/api/v2/user/{}/geolocation/'.format(user.id),
            headers=dict(
                Authorization=auth,
                Accept='application/json',
                ),
            )
    assert response.status_code == 200

    i = 0
    for k in ['leaf', 'node', 'top']:
        assert response.json['location'][i]['latitude'] == new_locations[k].latitude
        assert response.json['location'][i]['longitude'] == new_locations[k].longitude
        assert response.json['location'][i]['common_name'] == new_locations[k].common_name
        i += 1


def test_set_user_location(
        test_client,
        init_database,
        create_organisation,
        authed_sempo_admin_user,
        new_locations,
        create_temporary_extended_user,
        ):


    # create organisation
    organisation = create_organisation
    organisation.external_auth_password = config.EXTERNAL_AUTH_PASSWORD

    # create admin
    admin = authed_sempo_admin_user
    admin.set_held_role('ADMIN', 'admin')

    # create user
    user = create_temporary_extended_user
    user.full_location = new_locations['leaf']
    db.session.commit()

    user.get_base_user().add_user_to_organisation(organisation, False)

    # get admin auth token
    auth = get_complete_auth_token(authed_sempo_admin_user)

    response = test_client.put(
            '/api/v2/user/{}/geolocation/'.format(user.id),
            headers=dict(
                Authorization=auth,
                Accept='application/json',
            ),
            content_type='application/json',
            follow_redirects=True,
            data=json.dumps({
                'location_id': new_locations['leaf'].id,
            }),
       )

    assert response.status_code == 204
    assert user.full_location == new_locations['leaf']
