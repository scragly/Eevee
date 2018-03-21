import os
import sys

import logging
from logging import handlers


def init_logger(data_dir, debug_flag=False):

    # setup discord logger
    discord_log = logging.getLogger("discord")
    discord_log.setLevel(logging.INFO)

    # setup eevee logger
    eevee_log = logging.getLogger("eevee")

    # setup log directory
    log_path = os.path.join(data_dir, 'logs')
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # file handler factory
    def create_fh(file_name):
        fh_path = os.path.join(log_path, file_name)
        return handlers.RotatingFileHandler(
            filename=fh_path, encoding='utf-8', mode='a',
            maxBytes=400000, backupCount=20)

    # set eevee log formatting
    log_format = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d: '
        '%(message)s',
        datefmt="[%d/%m/%Y %H:%M]")

    # create file handlers
    eevee_fh = create_fh('eevee.log')
    eevee_fh.setLevel(logging.INFO)
    eevee_fh.setFormatter(log_format)
    eevee_log.addHandler(eevee_fh)
    discord_fh = create_fh('discord.log')
    discord_fh.setLevel(logging.INFO)
    discord_fh.setFormatter(log_format)
    discord_log.addHandler(discord_fh)

    # create console handler
    console_std = sys.stdout if debug_flag else sys.stderr
    eevee_console = logging.StreamHandler(console_std)
    eevee_console.setLevel(logging.INFO if debug_flag else logging.ERROR)
    eevee_console.setFormatter(log_format)
    eevee_log.addHandler(eevee_console)
    discord_console = logging.StreamHandler(console_std)
    discord_console.setLevel(logging.ERROR)
    discord_console.setFormatter(log_format)
    discord_log.addHandler(discord_console)

    return eevee_log

class DBHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        # add database data submission bit here
        # db.DatabaseInterface
