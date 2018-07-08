import os
import redis
import pymongo
from datetime import datetime


class Config(object):
    base_folder = os.getcwd()
    # day_of_data = str(datetime.today())
    rds = redis.StrictRedis('127.0.0.1', 6379)
    client = pymongo.MongoClient("localhost", 27017)

    db = client.metro # 地铁的db
    db_evcard = client.evcard # evcard的db

    info_log_file = base_folder+'/log/yidong_info.log'
    error_log_file = base_folder+'/log/yidong_error.log'

    #evcard的距离
    evcard_distance = 800
    evcard_filds = [
        'shopName',
        'address',
        'shopDesc',
        'navigateAddress',
        'lat_bd',
        'long_bd'
    ]
    base_folder_yidong = '/home/yidong_linux/yidong_linux/data'


class Config_dev(Config):
    day_of_data = '2018-05-31'
    # base_folder_yidong = '/home/hyfgreg/yidong_algo_demo/data'