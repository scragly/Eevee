import os
import sys

import logging
from logging import handlers


def init_logger(debug_flag=False):
    log_level = logging.INFO if debug_flag else logging.WARNING

    # d_py logs
    discord_log = logging.getLogger("discord")
    discord_log.setLevel(log_level)
    console = logging.StreamHandler()
    console.setLevel(log_level)
    discord_log.addHandler(console)

    # eevee logs
    logger = logging.getLogger("eevee")

    eevee_format = logging.Formatter(
        '%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d: '
        '%(message)s',
        datefmt="[%d/%m/%Y %H:%M]")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(eevee_format)
    logger.setLevel(log_level)

    if not os.path.exists('./logs/'):
        os.makedirs('./logs/')

    logfile_path = './logs/eevee.log'
    fhandler = handlers.RotatingFileHandler(
        filename=str(logfile_path), encoding='utf-8', mode='a',
        maxBytes=400000, backupCount=20)
    fhandler.setFormatter(eevee_format)

    logger.addHandler(fhandler)
    if debug_flag:
        logger.addHandler(stdout_handler)

    return logger

class DBHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        # add database data submission bit here
        # db.DatabaseInterface
