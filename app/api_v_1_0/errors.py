from . import api
from flask import jsonify


@api.app_errorhandler(404)
def page_not_found(e):
    respone = jsonify({'status':404,'result':str(e)})
    respone.status_code = 404
    return respone

@api.app_errorhandler(500)
def internal_server_error(e):
    respone = jsonify({'status': 500, 'result': str(e)})
    respone.status_code = 500
    return respone