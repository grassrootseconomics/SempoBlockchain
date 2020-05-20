from server.api2.geolocation_legacy_api import geolocation_legacy_blueprint

def do(app=None):
    api_prefix = '/api/v2'
    app.register_blueprint(geolocation_legacy_blueprint, url_prefix=api_prefix)
