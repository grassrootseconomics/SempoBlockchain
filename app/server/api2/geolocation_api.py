# standard imports
import logging

# third party imports
from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

# platform imports
from server import db
from server.utils.auth import requires_auth
from share.models.location import Location
from share.location.validate import valid_location_name, valid_coordinate
from share.location.osm import osm_resolve_name, osm_valid_data
from share.location.enum import LocationExternalSourceEnum

logg = logging.getLogger()

geolocation_blueprint = Blueprint('v2_geolocation', __name__)

def osm_storage_callback(place_id):
    location = Location.get_by_custom('place_id', place_id)
    return location

class LocationAPI(MethodView):

    def get(self, common_name):
        if not valid_location_name(common_name):
            response_object = {
                'message': 'Invalid location name: {}'.format(common_name)
            }
            return make_response(jsonify(response_object)), 400

        response_object = {
            'search_string': common_name,
            'local': [],
                }
        locations = Location.query.filter(Location.common_name==common_name)
        for location in locations:
            response_object['local'].append({
                'id': location.id,
                'common_name': location.common_name,
                'path': str(location),
                }
                )

        logg.debug('response object {}'.format(response_object))
        return make_response(jsonify(response_object)), 200


    def post(self):
        # get the input data
        post_data = request.get_json()
        latitude = post_data.get('latitude')
        longitude = post_data.get('longitude')
        common_name = post_data.get('common_name')
        response_object = None

        # check coordinates and name
        if not valid_coordinate(latitude, longitude):
            response_object = {
                'message': 'Invalid coordinate format',
            }
            return make_response(jsonify(response_object)), 400
        if not valid_location_name(common_name):
            response_object = {
                'message': 'Invalid location name',
            }
            return make_response(jsonify(response_object)), 400

        # if parent is given, check that it exists
        parent_location = None
        try:
            parent_id = post_data['parent_id']
            logg.debug('have parent id {}'.format(parent_id))
            parent_location = Location.query.get(parent_id)
            if parent_location == None:
                response_object = {
                    'message': 'parent id {} does not match any objects'.format(parent_id),
                   }
                return make_response(jsonify(response_object)), 400
        except KeyError:
            pass

        location = Location(common_name, latitude, longitude) 

        # if osm is given, check that the data is valid
        osm = post_data.get('osm')
        if osm != None and not osm_valid_data(osm):
            response_object = {
                    'message': 'invalid osm extension data',
                   }
            return make_response(jsonify(response_object)), 400
            location.add_external_data(LocationExternalSourceEnum.OSM, osm)

        db.session.add(location)
        db.session.commit()
        db.session.flush()

        response_object = {
                'message': 'location successfully added',
                'data': {
                    'location': {
                        'id': location.id,
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'common_name': location.common_name,
                        'path': str(location),
                        'osm': {},
                        },
                    },
                }
        if osm != None:
            response_object['data']['location']['osm']['place_id'] = osm['place_id'] 
            response_object['data']['location']['osm']['osm_id'] = osm['osm_id'] 

        return make_response(jsonify(response_object)), 201

geolocation_blueprint.add_url_rule(
        '/geolocation/<string:common_name>/',
    view_func=LocationAPI.as_view('v2_geolocation_local_view'),
    methods=['GET']
)

geolocation_blueprint.add_url_rule(
        '/geolocation/',
    view_func=LocationAPI.as_view('v2_geolocation_add_view'),
    methods=['POST']
)
