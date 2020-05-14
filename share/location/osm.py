"""Worker task for resolving location data from openstreetmap.

Adds location and its parent relations to database.
"""

# standard imports
import urllib
import requests
import logging
import json
import sys

logg = logging.getLogger(__file__)
logg.debug(sys.path)
# platform imports
import config
from server import db
from server.models.location import Location, LocationExternal
from share.location.enum import LocationExternalSourceEnum, osm_extension_fields

# local imports
from .constants import QUERY_TIMEOUT, DEFAULT_COUNTRY_CODE, VALID_OSM_ENTRY_TYPES



def osm_get_detail(place_id : int):

    url = 'https://nominatim.openstreetmap.org/details?format=json&linkedplaces=1&place_id=' 

    # build and perform osm query
    response = requests.get('{}{}'.format(url, place_id), timeout=QUERY_TIMEOUT)
    if response.status_code != 200:
        e = LookupError('failed request to openstreetmap; status code {}'.format(response.status_code))
        raise(e)
    response_json = json.loads(response.text)
    logg.debug(response_json)
    return response_json


# TODO: this is a standalone tool and should reside in a commonly available location
def osm_get_place_hierarchy(place_id : int):
    """Retrieves details from the OSM HTTP endpoint of the matching place_id,
    and recursively retrieves its parent relation places.

    Parameters
    ----------
    place_id : int
        osm place_id of start node

    Returns
    -------
    locations : list
        all resolved locations as Location model objects not already existing in database,
        in hierarchical order from lowest (start node) to highest
    """

    locations = []

    # iterate until parent relation is 0
    next_place_id = place_id
    while next_place_id != 0:

        # check if data already exists, if so, return prematurely as within that location relation
        # the caller has everything it nneeds
        ext_data = {}
        r = Location.get_by_custom(LocationExternalSourceEnum.OSM, 'place_id', next_place_id)
        if r != None:
            #locations.append(r[0])
            locations.append(r)
            break
       
        response_json = osm_get_detail(next_place_id)
        current_place_id = next_place_id
        next_place_id = response_json['parent_place_id']
        if response_json['type'] == 'unclassified':
            logg.debug('place id {} is unclassified, get parent {}'.format(current_place_id, next_place_id))
            continue
       
        # create new location object and add it to list of
        # new locations not already in database
        new_location = Location(
                response_json['names']['name'],
                response_json['centroid']['coordinates'][0],
                response_json['centroid']['coordinates'][1]
                )
        for field in osm_extension_fields:
            ext_data[field] = response_json[field]

        new_location.add_external_data(LocationExternalSourceEnum.OSM, ext_data)
        locations.append(new_location)

    return locations


def osm_resolve_name(name, country=DEFAULT_COUNTRY_CODE):
    """Searches the OSM HTTP endpoint for a location name. If a match is found
    the location hierarchy is built and committed to database.

    Parameters
    ----------
    name : str
        name to search
    country : str
        country filter (default: const DEFAULT_COUNTRY_CODE)
    
    Returns
    -------
    location : Location
        created / retrieved location object. If none is found, None is returned.
    """

    # build osm query
    q = {
            'format': 'json',
            'dedupe': 1,
            'country': country, 
            'q': name,
            }
    if getattr(config, 'EXT_OSM_EMAIL', None):
        q['email'] = config.EXT_OSM_EMAIL
    q = urllib.parse.urlencode(q)

    # perform osm query
    url = 'https://nominatim.openstreetmap.org/search?' + q
    try:
        response = requests.get(url, timeout=QUERY_TIMEOUT)
    except requests.exceptions.Timeout:
        logg.warning('request timeout to openstreetmap; {}:{}'.format(country, name))
        # TODO: re-insert task
        return None
    if response.status_code != 200:
        logg.warning('failed request to openstreetmap; {}:{}'.format(country, name))
        return None

    response_json = json.loads(response.text)
    logg.debug(response_json)

    # identify a suitable record among those returned
    place_id = 0
    for place in response_json:
        if place['type'] in VALID_OSM_ENTRY_TYPES:
            place_id = place['place_id']
    if place_id == 0:
        logg.debug('no suitable record found in openstreetmap for {}:{}'.format(country, name))
        return None

    # get related locations not already in database
    locations = []
    try:
        locations = osm_get_place_hierarchy(place_id)
    except LookupError as e:
        logg.warning('osm hierarchical query for {}:{} failed (response): {}'.format(country, name, e))
    except requests.exceptions.Timeout as e:
        logg.warning('osm hierarchical query for {}:{} failed (timeout): {}'.format(country, name, e))
                 
    # set hierarchical relations and store in database
    for i in range(len(locations)-1):
        locations[i].set_parent(locations[i+1])
        db.session.add(locations[i])
    db.session.commit()

    return locations[0]


def osm_resolve_coordinates(latitude, longitude):
  
    q = {
        'format': 'json',
        'lat': latitude,
        'lon': longitude,
    }

    if getattr(config, 'EXT_OSM_EMAIL', None):
        q['email'] = config.EXT_OSM_EMAIL
    q = urllib.parse.urlencode(q)

    # perform osm query
    url = 'https://nominatim.openstreetmap.org/reverse?' + q
    try:
        response = requests.get(url, timeout=QUERY_TIMEOUT)
    except requests.exceptions.Timeout:
        logg.warning('request timeout to openstreetmap; {}:{}'.format(country, name))
        # TODO: re-insert task
        return None
    if response.status_code != 200:
        logg.warning('failed request to openstreetmap; {}:{}'.format(country, name))
        return None

    response_json = json.loads(response.text)
    logg.debug(response_json)

    # identify a suitable record among those returned
    place_id = 0
    place = response_json
    #if place['osm_type'] in VALID_OSM_ENTRY_TYPES:
    place_id = place['place_id']
    if place_id == None or place_id == 0:
        logg.debug('no suitable record found in openstreetmap for N{}/E{}'.format(latitude, longitude))
        return None

    # skip the first entry if it is unclassified
    #response_json = osm_get_detail

    # get related locations not already in database
    locations = []
    try:
        locations = osm_get_place_hierarchy(place_id)
    except LookupError as e:
        logg.warning('osm hierarchical query for {}:{} failed (response): {}'.format(country, name, e))
    except requests.exceptions.Timeout as e:
        logg.warning('osm hierarchical query for {}:{} failed (timeout): {}'.format(country, name, e))
                 
    # set hierarchical relations and store in database
    for i in range(len(locations)-1):
        locations[i].set_parent(locations[i+1])
        db.session.add(locations[i])
    db.session.commit()

    return locations[0]
