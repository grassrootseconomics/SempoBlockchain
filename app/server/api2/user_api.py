# standard imports
import logging

# third party imports
from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

# platform imports
from server import db
from share.models.user import ExtendedUser
from server.utils.auth import requires_auth
from server.utils.access_control import AccessControl
from share import user as extended_user

logg = logging.getLogger()


class UserLocationAPI(MethodView):
    """Handles location-related operations on user

    Documentation is brief since it implmements standard flask blueprint interface
    """

    @requires_auth
    def get(self, user_id):
        """gets the stored location for the given user
        """
        if not AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'subadmin'}):
            return make_response(jsonify({
                'message': 'no clearance, clarence',
                }), 403)

        u = ExtendedUser.query.get(user_id)
        logg.debug('user {} -> {}'.format(user_id, u))

        response_object={
            'user_id': user_id,
            'location': [],
        }
        location = u.full_location
        while location != None:
            response_object['location'].append({
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'common_name': location.common_name,
                })
            location = location.parent

        return make_response(jsonify(response_object)), 200


    @requires_auth
    def put(self, user_id):
        if not AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'admin'}):
            return make_response(jsonify({
                'message': 'no clearance, clarence',
                }), 403)

        request_data = request.get_json()
        request_data['user_id'] = user_id

        try:
            extended_user.update(user_id, request_data)
        except:
            return make_response(jsonify({'message': 'invalid update data'})), 400
                
        # TODO: load full user data and return that
        return make_response(jsonify(request_data)), 204



user_blueprint = Blueprint('v2_user_geolocation', __name__)

user_blueprint.add_url_rule(
        '/user/<int:user_id>/geolocation/',
        view_func=UserLocationAPI.as_view('v2_user_geo|ocation_view'),
        methods=['GET', 'PUT'],
        )
