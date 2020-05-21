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
from share.location import osm
from share.location.enum import LocationExternalSourceEnum

logg = logging.getLogger()

geolocation_blueprint = Blueprint('v2_geolocation', __name__)


def osm_storage_callback(place_id):
    location = Location.get_by_custom('place_id', place_id)
    return location


# compiles a json api response from location object
def location_to_response_object(location):
    response_object = {
        'message': 'location successfully added',
        'data': {
            'location': {
                'id': location.id,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'common_name': location.common_name,
                'path': str(location),
                LocationExternalSourceEnum.OSM.name: {},
                },
            },
        }
    try:
        place_id = location.get_custom(LocationExternalSourceEnum.OSM, 'place_id')
        osm_id = location.get_custom(LocationExternalSourceEnum.OSM, 'osm_id')
        response_object['data']['location'][LocationExternalSourceEnum.OSM.name]['place_id'] = place_id
        response_object['data']['location'][LocationExternalSourceEnum.OSM.name]['osm_id'] = osm_id
    except:
        pass

    return response_object
    #if osm_data != None:
    #    response_object['data']['location'][LocationExternalSourceEnum.OSM.name]['place_id'] = osm_data['place_id'] 
    #    response_object['data']['location'][LocationExternalSourceEnum.OSM.name]['osm_id'] = osm_data['osm_id'] 


class LocationExternalAPI(MethodView):

    def get(self, ext_type, ext_id):
        if ext_type == LocationExternalSourceEnum.OSM.name:
            location = Location.get_by_custom(LocationExternalSourceEnum.OSM, 'place_id', ext_id)
            if location == None:
                response_object = {
                    'message': 'No stored OSM location match on place_id {}'.format(ext_id),
                }
                return make_response(jsonify(response_object)), 404
            response_object = location_to_response_object(location)
            return make_response(jsonify(response_object)), 200

        else:
            response_object = {
                'message': 'Unknown external source name {}'.format(ext_type),
            }
            return make_response(jsonify(response_object)), 400


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
                'latitude': location.latitude,
                'longitude': location.longitude,
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

        location = Location(common_name, latitude, longitude) 

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
            location.set_parent(parent_location)
        except KeyError:
            pass

        # if osm is given, check that the data is valid
        osm_data = post_data.get(LocationExternalSourceEnum.OSM.name)
        if osm_data != None:
            if not osm.valid_data(osm_data):
                response_object = {
                        'message': 'invalid osm extension data',
                       }
                return make_response(jsonify(response_object)), 400
            logg.debug('osm data {}'.format(osm_data))
            location.add_external_data(LocationExternalSourceEnum.OSM, osm_data)

        # flush to database
        db.session.add(location)
        db.session.commit()
        db.session.flush()

        response_object = location_to_response_object(location)
        return make_response(jsonify(response_object)), 201



geolocation_blueprint.add_url_rule(
        '/geolocation/<string:common_name>/',
    view_func=LocationAPI.as_view('v2_geolocation_local_view'),
    methods=['GET']
)

geolocation_blueprint.add_url_rule(
        '/geolocation/<string:ext_type>/<int:ext_id>/',
    view_func=LocationExternalAPI.as_view('v2_geolocation_local_external_view'),
    methods=['GET']
)

geolocation_blueprint.add_url_rule(
        '/geolocation/',
    view_func=LocationAPI.as_view('v2_geolocation_add_view'),
    methods=['POST']
)
