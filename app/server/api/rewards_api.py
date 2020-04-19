from flask import Blueprint
from flask import jsonify
from flask import make_response
from flask import request

from flask.views import MethodView

from server.utils.auth import requires_auth
from server.utils.rewards.processor import RewardsProcessor

rewards_blueprint = Blueprint('rewards', __name__)


class DisburseDailyBonusAPI(MethodView):
    @requires_auth(allowed_basic_auth_types='internal')
    def post(self):
        disbursement_data = request.get_json()

        created_since = disbursement_data.get('created_since')
        issuable_amount = disbursement_data.get('issuable_amount')
        transfer_amount = disbursement_data.get('transfer_amount')

        rewards_processor = RewardsProcessor(
            created_since=created_since,
            issuable_amount=issuable_amount,
            transfer_amount=transfer_amount
        )

        try:
            rewards_processor.disburse_daily_bonuses()
            response = {
                'message': 'Successfully disbursed daily bonuses.',
                'status': 'Success'
            }
            return make_response(jsonify(response), 200)
        except Exception as exception:
            response = {
                'error': {
                    'message': 'An error occurred: {}.'.format(exception),
                    'status': 'Fail'
                }
            }
            print(response)
            return make_response(jsonify(response), 500)


rewards_view = DisburseDailyBonusAPI.as_view('rewards_api_view')
rewards_blueprint.add_url_rule('/rewards/disburse_daily_bonuses/',
                               view_func=rewards_view,
                               methods=['POST'])
