from datetime import datetime
from datetime import timedelta

from server import db


def users_with_corresponding_total_outward_txs(created_since: int,
                                               transfer_amount: int):
    """
    This method queries the database for all unique outward transactions for each user and returns a list of tuples
    with a user id and the user's total unique outward transactions.
    Once the list of tuples as described above is obtained, the function computes the collective unique outward
    transactions value by iterating through the list.
    The function then finds a user corresponding to a user id in each tuple and replaces the user id value in the
    tuple with a user object.

    :param created_since: time in hours since the transaction was made
    :param transfer_amount: credit transfers amount
    :return: [(user_id, user_total_unique_outward_transactions)]
    """
    created_since = (datetime.now() - timedelta(hours=created_since))
    transfer_amount = (transfer_amount * 1e18)

    """
    Define SQL query with the following search criteria:
    SEARCH CRITERIA
        - count unique recipient user ids.
        - credit transfer amount is greater or equal to user defined wei.
        - credit transfer occurs since 24hrs ago.
        - credit transfer status is COMPLETE
        - transfer subtype STANDARD
    """
    sql_query = '''SELECT
    credit_transfer.sender_user_id,
    COUNT (DISTINCT (credit_transfer.recipient_user_id))
    FROM credit_transfer
    INNER JOIN transfer_account 
    ON credit_transfer.sender_transfer_account_id = transfer_account .id
    WHERE credit_transfer._transfer_amount_wei >= {}
    AND credit_transfer.created > '{}'
    AND credit_transfer.transfer_status = 'COMPLETE'
    AND credit_transfer.transfer_subtype = 'STANDARD'
    GROUP BY 
    credit_transfer.sender_user_id'''.format(transfer_amount, created_since)

    # execute query
    result = db.session.execute(sql_query)

    # get list of tuples with user ids and corresponding total unique outward transactions
    user_ids_with_total_unique_outward_transactions = result.fetchall()

    return user_ids_with_total_unique_outward_transactions
