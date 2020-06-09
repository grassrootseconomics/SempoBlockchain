# third-party imports
import pytest
from functools import partial
from faker import Faker
from faker.providers import phone_number

# platform imports
import config
from server import db, g
from share.models.location import Location
from share.models.user import ExtendedUser
from helpers.ussd_utils import make_kenyan_phone

fake = Faker()
fake.add_provider(phone_number)

@pytest.fixture(scope='module')
def create_user_phone():
    phone = partial(fake.msisdn)
    return make_kenyan_phone(phone())

@pytest.fixture(scope='module')
def create_temporary_extended_user(test_client, init_database, create_organisation, create_user_phone):
    # create organisation
    organisation = create_organisation
    organisation.external_auth_password = config.EXTERNAL_AUTH_PASSWORD

    # set active organisation
    g.active_organisation = organisation

    # create user without a transfer account
    temporary_first_name = 'Unknown first name'
    temporary_last_name = 'Unknown last name'
    temp_user = ExtendedUser(first_name=temporary_first_name,
                last_name=temporary_last_name,
                phone=create_user_phone,
                )

    organisation = g.active_organisation

    if organisation:
        temp_user.add_user_to_organisation(organisation, False)

    db.session.add(temp_user)
    db.session.commit()
    return temp_user

@pytest.fixture(scope='function')
def new_locations(test_client, init_database):

    locations = {}

    locations['top'] = Location('Croatia', 45.81318, 15.97624)
    db.session.add(locations['top'])

    locations['node'] = Location('Porec', 45.22738, 13.59569, locations['top'])
    db.session.add(locations['node'])

    locations['leaf'] = Location('Nice beach', 45.240173511, 13.597673455, locations['node'])
    db.session.add(locations['leaf'])
 
    db.session.commit()

    return locations
