# third party imports
from flask import Blueprint, make_response, jsonify
from flask.views import MethodView

# platform imports
from server import db
from server.models.user import User
from server.utils.auth import requires_auth

geolocation_legacy_blueprint = Blueprint('v2_geolocation_legacy', __name__)


class GetLegacyLocation(MethodView):
    """Handles operations on the legacy location fields in the user table
    """

    @requires_auth
    def get(self, user_id):
        """Retrieves legacy location information for a user
        """
        user = User.query.get(user_id)
        response_object = {
                'data': {
                    'lat': user.lat,
                    'lng': user.lng,
                    'location': user._location,
                    },
                }
        return make_response(jsonify(response_object)), 200

    def delete(self, user_id):
        """Nullifies legacy location information for a user
        """
        user = User.query.get(user_id)
        user._location = None
        db.session.add(user)
        db.session.commit()
        response_object = {
            'message': 'legacy location nulled',
                }
        return make_response(jsonify(response_object)), 204



geolocation_legacy_blueprint.add_url_rule(
        '/geolocation/legacy/user/<int:user_id>/',
    view_func=GetLegacyLocation.as_view('v2_geolocation_legacy_user_view'),
    methods=['GET']
)

geolocation_legacy_blueprint.add_url_rule(
        '/geolocation/legacy/user/<int:user_id>/',
    view_func=GetLegacyLocation.as_view('v2_geolocation_legacy_user_delete_view'),
    methods=['DELETE']
)
