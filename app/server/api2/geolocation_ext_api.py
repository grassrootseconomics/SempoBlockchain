# third party imports
from flask import Blueprint, make_response, jsonify
from flask.views import MethodView

# platform imports
from server import db
from server.models.user import User
from server.utils.auth import requires_auth

geolocation_ext_blueprint = Blueprint('geolocation_ext', __name__)

class GetLegacyLocation(MethodView):

    @requires_auth
    def get(self, user_id):
        user = User.query.get(user_id)
        response_object = {
                "lat": user.lat,
                "lng": user.lng,
                "location": user._location,
                }
        return make_response(jsonify(response_object)), 200

geolocation_ext_blueprint.add_url_rule(
        '/geolocation/user/<int:user_id>/',
    view_func=GetLegacyLocation.as_view('geolocation_ext_user_view'),
    methods=['GET']
)
