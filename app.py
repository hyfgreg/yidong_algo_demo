import datetime
import json

from flask import Flask, jsonify,request
from flask_request_params import bind_request_params
from util_v_0_1.func import plan_trip

app = Flask(__name__)
app.before_request(bind_request_params)
app.config['JSON_AS_ASCII'] = False

@app.route('/plan_trip')
def plane_trip():
    params = request.params
    o_lng = float(params['o_lng'])
    o_lat = float(params['o_lat'])
    d_lng = float(params['d_lng'])
    d_lat = float(params['d_lat'])
    otime = params['otime']
    trip = plan_trip(o_lat,o_lng,d_lat,d_lng,otime)
    print(trip)
    return jsonify(trip)

if __name__ == '__main__':
    app.run(debug=True)
