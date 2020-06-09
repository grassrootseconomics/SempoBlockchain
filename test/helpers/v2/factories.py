# framework imports
from factory.alchemy import SQLAlchemyModelFactory

# platform imports
from server import db
from share.models.user import ExtendedUser
from share.models.location import Location

class ExtendedUserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = ExtendedUser
        sqlalchemy_session = db.session

class LocationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Location
        sqlalchemy_session = db.session
