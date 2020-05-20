from server.api2.geolocation_ext_api import geolocation_ext_blueprint

def do(app=None):
    api_prefix = '/api/v2'
    app.register_blueprint(geolocation_ext_blueprint, url_prefix=api_prefix)
