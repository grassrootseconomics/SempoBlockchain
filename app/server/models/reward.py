from typing import Dict
from sqlalchemy.dialects.postgresql import JSONB

from server import db
from server.models.utils import ModelBase


class Reward(ModelBase):
    __tablename__ = 'reward'

    tag = db.Column(db.String)
    recipients_data = db.Column(JSONB, default={})

    def enter_recipient_data(self, recipient_data: Dict):
        """
        This method expects a dictionary with key value pairs of recipient data
        """
        # correct values in db in case a null value is returned
        if not self.recipients_data:
            self.recipients_data = {}

        # iterate through dictionary and enter data into db
        for data_key, data_value in recipient_data.items():
            self.recipients_data[data_key] = data_value
