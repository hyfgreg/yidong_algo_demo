from . import api
from flask import request, jsonify, url_for, redirect, current_app,abort
import datetime
# from flask_request_params import bind_request_params
# from util_v_0_6.func import plan_trip as pt
# from config import Config_dev
from mylogger.mylogger import mylogger

@api.before_request
def check_data():
    if not current_app.algo.data_ready:
        # data_ready为false，表示没有读取数据！需要重新读取数据！
        try:
            current_app.algo.day_of_data = datetime.date.today()
            current_app.algo.init_set()
            if current_app.algo.data_ready == False:
                raise FileNotFoundError
        except FileNotFoundError:
            # 假设是今天的数据还未更新，则选择上周的数据，但是day_of_data设置为上周
            try:
                today = datetime.date.today()
                sevenday = datetime.timedelta(days=7)
                last_week = today - sevenday
                current_app.algo.init_set(last_week)
                current_app.algo.day_of_data = last_week
                if current_app.algo.data_ready == False:
                    raise FileNotFoundError
            except FileNotFoundError:
                mylogger.error(message='驿动数据缺失！{}及其{}，请更新！{}'.format(today,last_week,'check_data'))
                return jsonify({'status':0,'result':'','info':'数据更新中，请稍后!'})
    else:
        # 数据是读取了的，需要判断是不是今天的！
        if not current_app.algo.day_of_data == datetime.date.today():
            #不是今天，首先判断是不是00:02之前，此时数据可能还未更新
            now = datetime.datetime.now()
            if now.hour < 1 and now.minute < 2:
                if now.day in [0,5]:
                    #如果是周一或者周六，昨天的数据是有问题，所以就必须用上周的
                    try:
                        today = datetime.date.today()
                        sevenday = datetime.timedelta(days=7)
                        last_week = today - sevenday
                        current_app.algo.init_set(last_week)
                        current_app.algo.day_of_data = last_week
                        #其他日子的话，认为此时的数据是昨天的，昨天和今天的数据比较类似，就不更新数据了，但是此时day_of_data还是昨天，下一次访问还是有可能是要更新数据的
                        if current_app.algo.data_ready == False:
                            raise FileNotFoundError
                    except FileNotFoundError:
                        mylogger.error(message='驿动数据缺失！{}及其{}，请更新！{}'.format(today,last_week,'check_data'))
                        return jsonify({'status': 0, 'result': '', 'info': '数据更新中，请稍后!'})
            else:
                try:
                    today = datetime.date.today()
                    current_app.algo.update_data()
                    if current_app.algo.data_ready == True:
                        current_app.algo.day_of_data = today
                    else:
                        raise FileNotFoundError
                except FileNotFoundError:
                    mylogger.error(message='驿动数据缺失！{}数据缺失，请更新！{}'.format(today,'check_data'))




# @api.before_request
# def check_args():
#     params = request.params
#     try:
#         o_lng = float(params['o_lng'])
#         o_lat = float(params['o_lat'])
#         d_lng = float(params['d_lng'])
#         d_lat = float(params['d_lat'])
#         otime = params['otime']
#         # membertype = int(params['membertype'])
#     except KeyError:
#         return redirect(url_for('api.lack_args'))

@api.route('/')
def test():
    # mylogger.info('test')
    # mylogger.error('test')
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
        membertype = int(params['membertype'])
    except KeyError:
        # 默认使用0
        membertype = 0

    # mylogger.info()

    trip = current_app.algo.plan_trip(o_lat, o_lng, d_lat, d_lng, otime)

    result = {'status':1,'result':trip,'info':'ok'}

    message = 'from: {},{} - to: {},{} - time: {}'.format(o_lat,o_lng,d_lat,d_lng,otime)
    mylogger.info(message)

    return jsonify(result)

@api.route('/lack_args')
def lack_args():
    result = {'status':0,'result':'','info':'缺少参数'}
    return jsonify(result)