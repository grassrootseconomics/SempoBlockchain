# standard imports
import os
import time

# third party imports
from flask import Blueprint, make_response, jsonify, current_app
from flask.views import MethodView

phone_blueprint = Blueprint('v2_phone', __name__)


class GetSMSLog(MethodView):
    """Outputs chronologically newest first all sms messages in local log file
    """
   
    def get(self, limit=0):
        sms_path = os.path.join(current_app.config['SYSTEM_DIR_VAR'], 'sms')
        files = os.listdir(sms_path)
        files.sort()
        content = ''
        if limit == 0:
            limit = len(files)
        for i in range(limit):
            f = files[i]
            fparts = f.split('_')
            t = time.strptime(fparts[0], '%Y%m%d%H%M%S%f')
            fpath = os.path.join(sms_path, f)
            fo = open(fpath, 'r')
            msg = fo.read()
            fo.close()
            content += '{} +{}: {}\n'.format(time.asctime(t), fparts[1], msg)
        resp = make_response(content)
        resp.headers['Content-Type'] = 'text/plain'
        return resp

phone_blueprint.add_url_rule(
        '/sms/',
    view_func=GetSMSLog.as_view('v2_phone_sms_list'),
    methods=['GET']
)

