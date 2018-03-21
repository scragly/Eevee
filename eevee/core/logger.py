import asyncio
import os
import sys

import time
import logging
from logging import handlers

from eevee.utils import snowflake

get_id = snowflake.create()

LOGGERS = ('eevee_logs', 'discord_logs')

def init_logger(bot, debug_flag=False):

    # setup discord logger
    discord_log = logging.getLogger("discord")
    discord_log.setLevel(logging.INFO)

    # setup eevee logger
    eevee_log = logging.getLogger("eevee")

    # setup log directory
    log_path = os.path.join(bot.data_dir, 'logs')
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

    # create db handler
    eevee_db = DBLogHandler(bot, 'eevee_logs')
    eevee_log.addHandler(eevee_db)
    discord_db = DBLogHandler(bot, 'discord_logs')
    discord_log.addHandler(discord_db)

    return eevee_log

class DBLogHandler(logging.Handler):
    def __init__(self, bot, log_name: str, level=logging.INFO):
        if log_name not in LOGGERS:
            raise RuntimeError(f'Unknown Log Name: {log_name}')
        self.bot = bot
        self.loop = bot.loop
        self.log_name = log_name
        self._backlog = {}
        super().__init__(level=level)

    @property
    def logging_stmt(self):
        return self.bot.dbi.logging_stmts.get(self.log_name, None)

    def emit(self, record):
        record_id = next(get_id)
        if not self.logging_stmt:
            self._backlog[record_id] = record
        else:
            if self._backlog:
                self._process_backlog()

        asyncio.run_coroutine_threadsafe(
            self.submit_log(record_id, record), self.loop)

    def _process_backlog(self):
        for k, v in self._backlog.items():
            asyncio.run_coroutine_threadsafe(self.submit_log(k, v), self.loop)

    async def submit_log(self, log_id, record):
        values = (log_id, record.created, record.name, record.levelname,
                  record.pathname, record.module, record.funcName,
                  record.lineno, record.message)
        await self.logging_stmt.fetch(*values)
