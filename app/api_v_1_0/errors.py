from . import api
from flask import jsonify,request
from mylogger.mylogger import mylogger



@api.app_errorhandler(404)
def page_not_found(e):
    mylogger.error('url: {} - error: {}'.format(request.url,e))
    respone = jsonify({'status':0,'result':'','info':'找不到服务器'})
    respone.status_code = 200
    return respone

@api.app_errorhandler(500)
def internal_server_error(e):
    mylogger.error('url: {} - error: {}'.format(request.url,e))
    respone = jsonify({'status': 0, 'result': '','info':'服务器出错'})
    respone.status_code = 200
    return respone