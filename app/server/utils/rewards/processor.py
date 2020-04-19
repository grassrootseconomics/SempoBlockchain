import logging

from flask import g

logging.basicConfig(level=logging.DEBUG)
rewards_logger = logging.getLogger()

from server import db
from server.models.user import User
from server.models.reward import Reward
from server.models.organisation import Organisation
from server.models.token import Token
from server.utils.credit_transfer import make_payment_transfer
from server.utils.transfer_enums import TransferSubTypeEnum
from server.utils.rewards.queries import users_with_corresponding_total_outward_txs

REWARD_DATA_TAGS = ['DAILY_BONUS', 'FAILURE_POINT']


def get_user_by_id(user_id: int):
    """
    This method queries the database for a user with an id matching the one provided as an argument
    :param user_id: user's id
    :return: user object
    """
    user = User.query.get(user_id)
    if user:
        return user
    else:
        raise Exception('User with id {} not found'.format(user_id))


def get_user_token(token_id: int):
    """
    Gets the token for a specific transfer account
    :param token_id: user's token id
    :return: token object
    """
    token = Token.query.get(token_id)

    if token:
        return token
    else:
        raise Exception('No token found for token id {}'.format(token_id))


def get_admin_account_to_disburse():
    """
    This method gets all admin users for a specific organisation and uses the first admin account to disburse a specific
    amount.
    """
    # initialize organisation admins
    organisation_admins = []

    # get a user's default organisation
    user_organisation = Organisation.master_organisation()

    # iterates through the organisation's users to find admins
    for organisation_user in user_organisation.users:
        if organisation_user.has_admin_role:
            organisation_admins.append(organisation_user)

    if len(organisation_admins) > 0:
        # get first admin
        admin = organisation_admins[0]
        return admin
    else:
        raise ValueError('No admin users found to disburse.')


def persist_reward_data(recipients_data: dict, tag: str):
    """
    This methods saves reward data to the database
    :param recipients_data:
    :param tag:
    """
    if tag not in REWARD_DATA_TAGS:
        raise ValueError('Unsupported reward data tag.')

    reward = Reward(tag=tag)
    db.session.add(reward)
    reward.enter_recipient_data(recipients_data)
    db.session.commit()


def process_daily_bonus_query(daily_bonus_query_result: list):
    """
    This function processes the query result and returns an iterable object with suitable data for disbursing rewards.
    :param daily_bonus_query_result:
    :return:
    """

    # initialize collective unique transactions value at zero
    collective_unique_outward_transactions = 0

    # initialize an empty list to store user objects with corresponding total unique outward transactions
    user_and_total_unique_outward_transactions_list = []

    # cleaned list of tuples with user ids and corresponding total unique outward transactions
    processed_user_ids_with_total_unique_outward_transactions = []

    for counter, (user_id,
                  token_id,
                  user_total_unique_outward_txs) in enumerate(daily_bonus_query_result):
        # compute total unique outward transactions for all users
        collective_unique_outward_transactions += user_total_unique_outward_txs

        # convert list into python objects
        user_id_and_total_unique_outward_transactions_tuple = (user_id, user_total_unique_outward_txs)

        processed_user_ids_with_total_unique_outward_transactions.append(
            user_id_and_total_unique_outward_transactions_tuple)

        # find user by user id
        user = get_user_by_id(user_id)

        # get user's token
        user_token = get_user_token(token_id=token_id)

        # add tuple of user and corresponding total unique outward transaction to list
        user_and_total_unique_outward_transactions_list.append((user,
                                                                user_total_unique_outward_txs,
                                                                user_token))

    # persist reward data
    recipient_data = {
        'user_ids_with_total_unique_outward_txs': processed_user_ids_with_total_unique_outward_transactions,
        'collective_unique_outward_txs': collective_unique_outward_transactions
    }

    persist_reward_data(recipients_data=recipient_data, tag='DAILY_BONUS')

    return user_and_total_unique_outward_transactions_list, collective_unique_outward_transactions


def make_daily_bonus_disbursements(created_since: int, issuable_amount: int, transfer_amount: int):
    daily_bonus_query_result = users_with_corresponding_total_outward_txs(created_since, transfer_amount)

    # process daily bonus data
    user_and_total_unique_outward_txs_list, collective_unique_outward_txs = process_daily_bonus_query(
        daily_bonus_query_result=daily_bonus_query_result)

    # get disbursing admin
    disbursing_admin = get_admin_account_to_disburse()

    try:
        # iterate through list to make disbursements
        for counter, (user,
                      unique_outward_transactions_per_user,
                      user_token) in enumerate(user_and_total_unique_outward_txs_list):
            # compute user's total unique outward transactions as a percentage of the collective unique outward
            # transactions
            user_percentage_unique_outward_transactions = (
                (unique_outward_transactions_per_user / collective_unique_outward_txs))

            # get user's share of the total issuable amount
            user_bonus_amount = int(user_percentage_unique_outward_transactions * issuable_amount)

            if user_bonus_amount > 1:
                try:
                    disbursement = make_payment_transfer(user_bonus_amount,
                                                         send_user=disbursing_admin,
                                                         receive_user=user,
                                                         transfer_subtype=TransferSubTypeEnum.DISBURSEMENT,
                                                         token=user_token)

                    db.session.add(disbursement)
                    db.session.commit()

                    rewards_logger.info('DISBURSING: {} TO USER_ID: {}'.format(user_bonus_amount,
                                                                               user.id))
                except Exception as exception:
                    rewards_logger.error(
                        'DISBURSEMENT FAILED FOR USER_ID: {}, WITH ERROR: {}'.format(user.id,
                                                                                     exception))
                    disbursement_failure_point = {
                        'user_id': user.id,
                        'user_bonus_amount': user_bonus_amount
                    }

                    # persist failure point
                    persist_reward_data(recipients_data=disbursement_failure_point,
                                        tag='FAILURE_POINT')

    except Exception as exception:
        rewards_logger.error('AN ERROR OCCURRED: {}'.format(exception))


class RewardsProcessor:

    def __init__(self, created_since: int, issuable_amount: int, transfer_amount: int):
        self.created_since = created_since
        self.issuable_amount = issuable_amount
        self.transfer_amount = transfer_amount

    def disburse_daily_bonuses(self):
        g.show_all = True
        make_daily_bonus_disbursements(created_since=self.created_since,
                                       issuable_amount=self.issuable_amount,
                                       transfer_amount=self.transfer_amount)
