# standard imports
import logging

# platform imports
from server import db
from share import user as extended_user
from share.models.user import ExtendedUser

logg = logging.getLogger()


def test_extended_user_update_location(
    new_locations,
    create_temporary_extended_user,
        ):

    u = create_temporary_extended_user
    extended_user.update(u.id, {
        'location_id': new_locations['leaf'].id,
        })

    assert u.full_location == new_locations['leaf']
