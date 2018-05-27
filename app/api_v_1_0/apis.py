from . import api
from flask import request,jsonify,url_for,redirect
# from flask_request_params import bind_request_params
from util_v_0_4.func import plan_trip as pt
# from config import Config_dev


@api.route('/')
def test():
    return jsonify({'hello':'world'})

@api.route('/plan_trip')
def plan_trip():
    params = request.params
    try:
        o_lng = float(params['o_lng'])
        o_lat = float(params['o_lat'])
        d_lng = float(params['d_lng'])
        d_lat = float(params['d_lat'])
        otime = params['otime']
        # membertype = int(params['membertype'])
    except KeyError:
        return redirect(url_for('api.lack_args'))
    try:
        membertype = int(params['memvertype'])
    except KeyError:
        # 默认使用0
        membertype = 0

    trip = pt(o_lat, o_lng, d_lat, d_lng, otime)
    print(trip)
    result = {'status':1,'result':trip}
    return jsonify(result)

@api.route('/lack_args')
def lack_args():
    result = {'status':0,'result':'缺少参数'}
    return jsonify(result)