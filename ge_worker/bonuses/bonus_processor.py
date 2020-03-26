import os
import sys

from datetime import datetime
from datetime import timedelta
from flask import g
from logging import Logger

parent_dir = os.path.abspath(os.path.join(os.getcwd(), "../app"))
sys.path.append(parent_dir)
sys.path.append(os.getcwd())

from server import create_app, db
from server.models.user import User
from server.utils.credit_transfer import make_payment_transfer
from server.utils.transfer_enums import TransferSubTypeEnum


def get_user_by_id(user_id):
    user = User.query.get(user_id)
    if user:
        return user
    raise Exception('User with id {} not found'.format(user_id))


def get_list_of_users_with_total_unique_outward_transactions():
    """"
    This method queries the database for all unique outward transactions for each user and returns a list of tuples
    with a user id and the user's total unique outward transactions.
    [(user_id, user_total_unique_outward_transactions)]
    Once the list of tuples as described above is obtained, the function computes the collective unique outward
    transactions value by iterating through the list.
    The function then finds a user corresponding to a user id in each tuple and replaces the user id value in the
    tuple with a user object.

    returns [(user, user_total_unique_outward_transactions)]
    """

    """
    Define SQL query with the following search criteria:
    SEARCH CRITERIA
        - count unique recipient user ids.
        - credit transfer amount is greater or equal to 20wei.
        - credit transfer occurs since 24hrs ago.
        - credit transfer status is COMPLETE
        - transfer subtype STANDARD
    """
    sql_query = '''SELECT
    credit_transfer.sender_user_id,
    COUNT (DISTINCT (credit_transfer.recipient_user_id))
    FROM credit_transfer
    LEFT JOIN transfer_account 
    ON credit_transfer.sender_transfer_account_id = transfer_account .id
    WHERE credit_transfer._transfer_amount_wei >= (2*10e17)
    AND credit_transfer.created > '{}'
    AND credit_transfer.transfer_status = 'COMPLETE'
    AND credit_transfer.transfer_subtype = 'STANDARD'
    GROUP BY 
    credit_transfer.sender_user_id'''.format((datetime.now() - timedelta(hours=24)))

    # execute query
    result = db.session.execute(sql_query)

    # get list of tuples with user ids and corresponding total unique outward transactions
    user_ids_with_total_unique_outward_transactions = result.fetchall()

    # initialize collective unique transactions value at zero
    collective_unique_outward_transactions = 0

    # initialize an empty list to store user objects with corresponding total unique outward transactions
    user_and_total_unique_outward_transactions_list = []

    for counter, (user_id,
                  user_total_unique_outward_transactions) in enumerate(user_ids_with_total_unique_outward_transactions):
        # compute total unique outward transactions for all users
        collective_unique_outward_transactions += user_total_unique_outward_transactions

        # find user by user id
        user = get_user_by_id(user_id)

        # add tuple of user and corresponding total unique outward transaction to list
        user_and_total_unique_outward_transactions_list.append((user, user_total_unique_outward_transactions))

    return user_and_total_unique_outward_transactions_list, collective_unique_outward_transactions


class BonusProcessor:
    """
    This class is responsible for processing different bonus issuance and pre-scheduled incentive
    disbursements.
    """

    def __init__(self, issuable_amount):
        self.issuable_amount = issuable_amount

    def auto_disburse_amount(self):
        # provide flask context within which SQL queries can be executed.
        app = create_app()
        app_context = app.app_context()
        app_context.push()

        # set flask context to show all model data for easier querying using flask models.
        g.show_all = True

        # get list user objects with corresponding total unique outward transactions and collective unique outward
        # transactions
        user_and_total_unique_outward_transactions_list, collective_unique_outward_transactions \
            = get_list_of_users_with_total_unique_outward_transactions()

        # iterate through list to make disbursements
        for counter, \
            (user,
             unique_outward_transactions_per_user) in enumerate(user_and_total_unique_outward_transactions_list):
            # compute user's total unique outward transactions as a percentage of the collective unique outward
            # transactions
            user_percentage_unique_outward_transactions = (
                (unique_outward_transactions_per_user / collective_unique_outward_transactions))

            # get user's share of the total issuable amount
            user_bonus_amount = int(user_percentage_unique_outward_transactions * self.issuable_amount)

            # define logger
            print('USER: {} {}, '
                  'USER_TOTAL_UNIQUE_OUTWARD_TX: {}, '
                  'USER_PERCENTAGE_UNIQUE_OUTWARD_TX: {}, '
                  'USER_BONUS_AMOUNT: {} '.format(user.first_name,
                                                  user.last_name,
                                                  unique_outward_transactions_per_user,
                                                  user_percentage_unique_outward_transactions,
                                                  user_bonus_amount))

            if user_bonus_amount > 1:
                # TODO[Philip]: Results in a synchronous subtask 
                make_payment_transfer(user_bonus_amount,
                                      receive_user=user,
                                      transfer_subtype=TransferSubTypeEnum.DISBURSEMENT)

                db.session.commit()

        # pop flask application context
        app_context.pop()
