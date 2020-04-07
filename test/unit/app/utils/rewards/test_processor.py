from app.server.utils.rewards.processor import get_user_by_id
from app.server.utils.rewards.processor import get_transfer_account_token
from app.server.utils.rewards.processor import get_admin_account_to_disburse


def test_get_user_by_id(test_client, init_database, create_transfer_account_user):
    user = create_transfer_account_user
    assert user.id == get_user_by_id(1).id


def test_get_transfer_account_token(test_client, init_database, create_transfer_account):
    transfer_account = create_transfer_account
    token = get_transfer_account_token(transfer_account)
    assert token.name == 'AUD Reserve Token'


def test_get_admin_account_to_disburse(test_client,
                                       init_database,
                                       authed_sempo_admin_user,
                                       create_transfer_account_user):

    admin = get_admin_account_to_disburse(create_transfer_account_user)
    assert admin.email == authed_sempo_admin_user.email
