# standard imports
import os
import time

# third party imports
from flask import Blueprint, make_response, jsonify, current_app
from flask.views import MethodView

# platform imports
from server.utils.auth import requires_auth

phone_blueprint = Blueprint('v2_phone', __name__)


class GetSMSLog(MethodView):
    """Outputs chronologically newest first all sms messages in local log file
    """
  
    @requires_auth
    def get(self, limit=0):
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

phone_blueprint.add_url_rule(
        '/sms/',
    view_func=GetSMSLog.as_view('v2_phone_sms_list'),
    methods=['GET']
)

