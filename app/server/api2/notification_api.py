# standard imports
import os
import time

# third party imports
from flask import Blueprint, make_response, jsonify, current_app, request
from flask.views import MethodView

# platform imports
from server.utils.auth import requires_auth
from server.utils.phone import proccess_phone_number
from share.models.notification import Notification
from server.models.user import User

notification_blueprint = Blueprint('v2_notification', __name__)


class GetSMSLog(MethodView):
    """Outputs chronologically newest first all sms messages in notifications db log
    """

    @requires_auth
    def get(self, **kwargs):

        limit = 0
        if request.args.get('limit') != None:
            limit = int(request.args.get('limit'))

        phone = kwargs.get('phone')
        try:
            phone = proccess_phone_number(phone)
        except:
            return make_response(jsonify({}), 400)

        q = Notification.query
        if phone == None:
            user_id = kwargs.get('user_id')
            if user_id != None:
                user_id = int(user_id)

            if user_id != None:
                u = User.query.get(user_id)
                if u == None:
                    return make_response(jsonify({
                        'message': 'user {} not found'.format(user_id),
                        }), 404)
                if u.phone == None:
                    return make_response(jsonify({
                        'message': 'no phone registered for user {}'.format(user_id),
                        }), 400)
                phone = u.phone

        if phone != None:
            q = q.filter(Notification.recipient == phone)

        q = q.order_by(Notification.updated.desc())

        if limit > 0:
            q = q.limit(limit)
     
        response = []
        notifications = q.all()
        for n in notifications:
            response.append({
                'datetime': n.created,
                'number': n.recipient,
                'message': n.content,
                })
        
        return make_response(jsonify(response))

notification_blueprint.add_url_rule(
        '/sms/',
    view_func=GetSMSLog.as_view('v2_notification_sms_all'),
    methods=['GET']
)

notification_blueprint.add_url_rule(
        '/sms/user/<int:user_id>/',
    view_func=GetSMSLog.as_view('v2_notification_sms_user'),
    methods=['GET']
)

notification_blueprint.add_url_rule(
        '/sms/<string:phone>/',
    view_func=GetSMSLog.as_view('v2_notification_sms_phone'),
    methods=['GET']
)
