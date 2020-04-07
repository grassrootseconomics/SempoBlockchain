import config
import requests

from requests.auth import HTTPBasicAuth

from eth_manager import celery_app


@celery_app.task()
def disburse_daily_bonuses():
    app_host = config.APP_HOST

    created_since = config.TRANSFERS_CREATED_SINCE
    issuable_amount = config.ISSUABLE_REWARD_AMOUNT
    transfer_amount = config.TRANSFER_AMOUNT_LIMIT

    disbursement_data = {
        'created_since': created_since,
        'issuable_amount': issuable_amount,
        'transfer_amount': transfer_amount
    }

    response = requests.post(app_host + '/api/v1/rewards/disburse_daily_bonuses/',
                             auth=HTTPBasicAuth(config.INTERNAL_AUTH_USERNAME,
                                                config.INTERNAL_AUTH_PASSWORD),
                             json=disbursement_data)
