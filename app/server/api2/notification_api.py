# standard imports
import os
import time
import logging

# third party imports
from flask import Blueprint, make_response, jsonify, current_app
from flask.views import MethodView

# platform imports
from server.utils.auth import requires_auth
from server.utils.phone import proccess_phone_number
from share.models.notification import Notification
from server.models.user import User

logg = logging.getLogger()
notification_blueprint = Blueprint('v2_notification', __name__)


class GetSMSLog(MethodView):
    """Outputs chronologically newest first all sms messages in local log file
    """

    @requires_auth
    def get(self, **kwargs):
        limit = kwargs.get('limit')
        if limit == None:
            limit = 0
        else:
            limit = int(limit)

        phone = kwargs.get('phone')
        logg.debug('phone before {}'.format(phone))
        try:
            phone = proccess_phone_number(phone)
        except:
            return make_response(jsonify({}), 400)

        logg.debug('phone after {}'.format(phone))
        q = Notification.query
        if phone == None:
            user_id = kwargs.get('user_id')
            if user_id != None:
                user_id = int(user_id)

            if user_id != None:
                logg.debug('get user {}'.format(user_id))
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

        if limit > 0:
            q = q.limit(limit)
      
        logg.debug('query {}'.format(q))
        response = []
        notifications = q.all()
        for n in notifications:
            response.append({
                'datetime': n.created,
                'number': n.recipient,
                'content': n.content,
                })
        
        return make_response(jsonify(response))

notification_blueprint.add_url_rule(
        '/sms/',
    view_func=GetSMSLog.as_view('v2_notification_sms_all'),
    methods=['GET']
)

notification_blueprint.add_url_rule(
        '/sms/<int:user_id>/',
    view_func=GetSMSLog.as_view('v2_notification_sms_user'),
    methods=['GET']
)

notification_blueprint.add_url_rule(
        '/sms/<string:phone>/',
    view_func=GetSMSLog.as_view('v2_notification_sms_phone'),
    methods=['GET']
)

