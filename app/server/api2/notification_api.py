# standard imports
import os
import time
import logging

# third party imports
from flask import Blueprint, make_response, jsonify, current_app
from flask.views import MethodView

# platform imports
from server.utils.auth import requires_auth
#from server.utils.auth import requires_auth
from share.models.notification import Notification

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

       
        q = Notification.query
        if limit > 0:
            q = q.limit(limit)
       
        response = []
        notifications = q.all()
        for n in notifications:
            response.append({
                'datetime': n.created,
                'number': n.recipient,
                'content': n.content,
                })
        
        return make_response(jsonify(response))

    @requires_auth
    def _get_from_fs(self, **kwargs):
        return make_response(jsonify({
                'message': 'you are here, we are not',
                }), 400)
        limit = kwargs.get('limit')
        if limit == None:
            limit = 0
        else:
            limit = int(limit)

        logg.debug('vars u{} l{}'.format(kwargs.get('user_id'), limit))
        sms_path = os.path.join(current_app.config['SYSTEM_PATH']['sms'])
        files = os.listdir(sms_path)
        files.sort()
        content = ''
        if limit == 0:
            limit = len(files)
        for i in range(limit):
            f = files[i]
            (timestamp, number) = f.split('_')
            t = time.strptime(timestamp, '%Y%m%d%H%M%S%f')
            fpath = os.path.join(sms_path, f)
            fo = open(fpath, 'r')
            msg = fo.read()
            fo.close()
            content += '{} +{}: {}\n'.format(time.asctime(t), number, msg)
        resp = make_response(content)
        resp.headers['Content-Type'] = 'text/plain'
        return resp

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

