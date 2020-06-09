import enum

osm_extension_fields = ['osm_id', 'class', 'osm_type']

class LocationExternalSourceEnum(enum.Enum):
    OSM = 'OSM'
    GEONAMES = 'GEONAMES'

