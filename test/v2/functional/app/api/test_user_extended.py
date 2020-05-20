# standard imports
import json

# third-party imports
import pytest

# platform imports
import config
from server import db
from helpers.v2.factories import ExtendedUserFactory, LocationFactory
from server.utils.auth import get_complete_auth_token

def test_get_user_location(
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
