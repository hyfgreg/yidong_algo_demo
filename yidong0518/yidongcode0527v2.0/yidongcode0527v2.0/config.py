import os
from datetime import datetime


class Config(object):
    base_folder = os.getcwd()
    day_of_data = str(datetime.today())

class Config_dev(Config):
    day_of_data = '2018-05-18'