# third party imports
from flask import Blueprint, make_response, jsonify, g
from flask.views import MethodView

# platform imports
from server import db
from server.models.user import User
from server.utils.auth import requires_auth
from server.utils.access_control import AccessControl

geolocation_legacy_blueprint = Blueprint('v2_geolocation_legacy', __name__)


class GetLegacyLocation(MethodView):
    """Handles operations on the legacy location fields in the user table
    """

    @requires_auth
    def get(self, user_id):
        """Retrieves legacy location information for a user
        """
        if not AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'subadmin'}):
            return make_response(jsonify({
                'message': 'no clearance, clarence',
                }), 403)

        user = User.query.get(user_id)
        response_object = {
                "lat": user.lat,
                "lng": user.lng,
                "location": user._location,
                }
        return make_response(jsonify(response_object)), 200


geolocation_legacy_blueprint.add_url_rule(
        '/geolocation/legacy/user/<int:user_id>/',
    view_func=GetLegacyLocation.as_view('v2_geolocation_legacy_user_view'),
    methods=['GET']
)
