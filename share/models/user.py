# framework imports
from sqlalchemy.ext.hybrid import hybrid_property

# platform imports
from server import db
from server.models import user as base_user
from share.models.user_extension import UserExtension

class ExtendedUser(base_user.User):

    __mapper_args__ = {
        'polymorphic_identity':'extended_user',
            }
    _full_location = db.relationship(UserExtension)

    @hybrid_property
    def full_location(self):
        return self._full_location.location

    @full_location.setter
    def full_location(self, location):
        self._full_location.location = location

    def get_base_user(self):
        return super(ExtendedUser, self)
    
    def get_full_location(self):
        return self._full_location

    def __init__(self, blockchain_address=None, **kwargs):
        super(ExtendedUser, self).__init__(blockchain_address, **kwargs)
