import logging
from util_v_0_6.yidong_algo import YidongAlgo
from flask import Flask
from flask_request_params import bind_request_params

def create_app():
    app = Flask(__name__)

    app.before_request(bind_request_params)
    app.config['JSON_AS_ASCII'] = False

    from .api_v_1_0 import api as api_v_1_0_blueprint
    app.register_blueprint(api_v_1_0_blueprint)

    YidongAlgo.init(app)
    return app