"""Tests location data resource workers
"""

# standard imports
import logging

# third party imports
import pytest

# platform imports
import config
from server import db
from share.models.location import Location
from share.location import osm
from share.location.enum import LocationExternalSourceEnum

logg = logging.getLogger(__file__)


class LocationCacheControl:
    """callback function used in osm.resolve_name to check if record already exists in database

    Attributes
    ----------
    place_id : int
        the place_id of the encountered existing record
    location : Location
        the location object corresponding to the existing record
    """
    def __init__(self):
        self.place_id = 0
        self.location = None


    def have_osm_data(self, place_id):
        """Callback function used in osm.resolve_name to check if a record with osm place_id already exists.

        If a match is found, the place_id and location is stored in the object.

        Parameters
        ----------
        place_id : int
            osm place_id to check the database for

        Returns
        -------
        location : Location
            matched location object, None of no match
        """
        if self.location != None:
            raise RuntimeError('cached location already set')
        self.location = Location.get_by_custom(LocationExternalSourceEnum.OSM, 'place_id', place_id)
        if self.location != None:
            self.place_id = place_id
        return self.location



# TODO: improve by using object to hold cached location item which has have_osm_data as class method
def store_osm_data(location_data, cache):
    """Commits to database hierarchical data retrieved from the osm name resolve tool
       
    Parameters
    -----------
    location_data : dict
        location data as returned from osm.resolve_name
    cache : LocationCacheControl
        provides callback function used in osm.resolve_name to check if record already exists in database
         
    Returns
    -------
    locations : list
        list of location objects added to database
    """

    locations = []

    for i in range(len(location_data)):
        location = None
        if cache.location != None:
            if location_data[i]['ext_data']['place_id'] == cache.place_id:
                location = Location.get_by_custom(LocationExternalSourceEnum.OSM, 'place_id', location_data[i]['ext_data']['place_id'])
        if location == None:
            location = Location(
                location_data[i]['common_name'],
                location_data[i]['latitude'],
                location_data[i]['longitude'],
                    )
            location.add_external_data(LocationExternalSourceEnum.OSM, location_data[i]['ext_data'])
        locations.append(location)
    
    for i in range(len(locations)):
        location = locations[i]
        if location.location_external[0].external_reference['place_id'] == cache.place_id:
            break
        if i < len(locations)-1:
            locations[i].set_parent(locations[i+1])
        db.session.add(locations[i])
    db.session.commit()
    return locations



def test_get_osm_cascade(test_client, init_database):
    """
    GIVEN a search string
    WHEN hierarchical matches exist in osm for that string
    THEN check that location and relations are correctly returned
    """

    cache = LocationCacheControl()
    q = 'mnarani'
    location_data = osm.resolve_name(q, storage_check_callback=cache.have_osm_data)
    locations = store_osm_data(location_data, cache)
    
    leaf = locations[0]
    assert leaf != None
    assert leaf.common_name.lower() == q

    parent = leaf.parent
    assert parent.common_name.lower() == 'kilifi'

    parent = parent.parent
    assert 'kenya' in parent.common_name.lower() 



def test_get_osm_cascade_coordinates(test_client, init_database):
    """
    GIVEN coordinates
    WHEN hierarchical matches exist in osm for that coordinates
    THEN check that location and relations are correctly returned
    """

    cache = LocationCacheControl()
    q = 'mnarani'
    latitude = -3.6536
    longitude = 39.8512
    location_data = osm.resolve_coordinates(latitude, longitude, storage_check_callback=cache.have_osm_data)
    locations = store_osm_data(location_data, cache)

    leaf = locations[0]
    assert leaf != None
    assert leaf.common_name.lower() == q

    parent = leaf.parent
    assert parent.common_name.lower() == 'kilifi'

    parent = parent.parent
    assert 'kenya' in parent.common_name.lower() 

