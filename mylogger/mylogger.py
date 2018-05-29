import logging
from config import Config_dev

handlers = {
    logging.INFO:Config_dev.info_log_file,
    logging.ERROR:Config_dev.error_log_file
}

def createHanlders():
    logLevels = handlers.keys()
    for level in logLevels:
        path = handlers[level]
        handlers[level] = logging.FileHandler(path)

createHanlders()

logging_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# logging.basicConfig(format=logging_format,level=logging.INFO)

class MyLogger(object):
    def __init__(self):
        self.__loggers = {}
        for level,handler in handlers.items():
            logger = logging.getLogger(str(level))
            handler.setFormatter(logging_format)
            logger.addHandler(handler)
            logger.setLevel(level)
            self.__loggers.update({level:logger})

    def info(self,message):
        self.__loggers[logging.INFO].info(message)

    def error(self,message):
        self.__loggers[logging.ERROR].error(message)

mylogger = MyLogger()


