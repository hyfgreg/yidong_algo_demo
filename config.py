import os
import redis
import pymongo
from datetime import datetime


class Config(object):
    base_folder = os.getcwd()
    # day_of_data = str(datetime.today())
    rds = redis.StrictRedis('127.0.0.1', 6379)
    client = pymongo.MongoClient("localhost", 27017)
    db = client.metro

    info_log_file = base_folder+'/log/yidong_info.log'
    error_log_file = base_folder+'/log/yidong_error.log'

class Config_dev(Config):
    day_of_data = '2018-05-29'
    base_folder = '/home/yidong_linux/yidong_linux/data'