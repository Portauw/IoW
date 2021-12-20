import base_config
from config import cfg
import logging
import os
import sys
from datetime import datetime
#from pythonjsonlogger import jsonlogger

LOG_LEVEL = logging.DEBUG

def debug():
    global LOG_LEVEL
    LOG_LEVEL = logging.DEBUG


def info():
    global LOG_LEVEL
    LOG_LEVEL = logging.INFO


def warning():
    global LOG_LEVEL
    LOG_LEVEL = logging.WARNING


def error():
    global LOG_LEVEL
    LOG_LEVEL = logging.ERROR


levels = {
    'debug': debug,
    'info': info,
    'warning': warning,
    'error': error
}

levels.get(os.environ.get('LOG_LEVEL', 'debug').lower())()

class My_Formatter(logging.Formatter):
    def __init__(self, fmt="%(asctime)s %(levelname)s: %(message)s", *args, **kwargs):
        logging.Formatter.__init__(self, fmt=fmt, *args, **kwargs)

    def format(self, record):
        #result = super().format(record)
        #record.msg = "floep" + record.msg
        return super(My_Formatter, self).format(record)

#class StackDriverJsonFormatter(jsonlogger.JsonFormatter, object):
#    def __init__(self, fmt="%(levelname) %(datetime) %(message)", style='%', *args, **kwargs):
#        jsonlogger.JsonFormatter.__init__(self, fmt=fmt, *args, **kwargs)
#
#    def process_log_record(self, log_record):
#        log_record['datetime'] = datetime.now()
#        log_record['type'] = "application"
#        log_record['severity'] = log_record['levelname']
#        del log_record['levelname']
#
#        return super(StackDriverJsonFormatter, self).process_log_record(log_record)

# assemble logger structure
logger = logging.getLogger()

handler_formatter = My_Formatter()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(handler_formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

#if cfg.logging_file_absolute_path:
#    file_handler_formatter = My_Formatter()
#    file_handler = logging.FileHandler(cfg.logging_file_absolute_path)
#    file_handler.setFormatter(file_handler_formatter)
#    file_handler.setLevel(logging.DEBUG)
#    logger.addHandler(file_handler)

logger.setLevel(LOG_LEVEL)
