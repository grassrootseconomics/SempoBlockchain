"""Tests location data resource workers
"""

# standard imports
import logging

# third party imports
import pytest

# platform imports
import config
from server.models.location import Location
from share.location.osm import osm_resolve_name, osm_resolve_coordinates

logg = logging.getLogger(__file__)


def test_get_osm_cascade(test_client, init_database):
    """
    GIVEN a search string
    WHEN hierarchical matches exist in osm for that string
    THEN check that location and relations are correctly stored in models
    """

    q = 'mnarani'
    leaf = osm_resolve_name('mnarani')
    assert leaf != None
    assert leaf.common_name.lower() == q

    parent = leaf.parent
    assert parent.common_name.lower() == 'kilifi'

    parent = parent.parent
    assert 'kenya' in parent.common_name.lower() 
    logg.debug('leaf {} parent {}'.format(leaf, parent))

def test_get_osm_cascade_coordinates(test_client, init_database):
    """
    GIVEN a search string
    WHEN hierarchical matches exist in osm for that string
    THEN check that location and relations are correctly stored in models
    """

    q = 'mnarani'
    latitude = -3.6536
    longitude = 39.8512
    leaf = osm_resolve_coordinates(latitude, longitude)
    assert leaf != None
    assert leaf.common_name.lower() == q

    parent = leaf.parent
    assert parent.common_name.lower() == 'kilifi'

    parent = parent.parent
    assert 'kenya' in parent.common_name.lower() 
    logg.debug('leaf {} parent {}'.format(leaf, parent))

