# platform includes
from server import db
from share.models.user import ExtendedUser
from share.models.location import Location


def update_user_location(u : ExtendedUser, location_id : int):
    location = Location.query.get(location_id)
    if location == None:
        raise ValueError('location id {} not found'.format(location_id))
    u.full_location = location


def update(user_id : int, fields : dict):

    u = ExtendedUser.query.get(user_id)
    if u == None:
        raise ValueError('user id {} not found'.format(user_id))

    user_location = Location.query.get(fields['location_id'])
    if user_location == None:
        raise ValueError('unknown location id {}'.format(fields['location_id']))

    if fields.get('location_id') != None:
        update_user_location(u, fields['location_id'])
        u._location = user_location.common_name
        u.latitude = user_location.latitude
        u.longitude = user_location.longitude
        
    db.session.add(u)
    db.session.commit()
