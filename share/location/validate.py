def valid_location_name(common_name):
    return True


def valid_coordinate(x, y):
    return isinstance(x, float) and isinstance(y, float)
