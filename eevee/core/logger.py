import asyncio
import os
import sys
import json
import time
from datetime import timezone
import logging
from logging import handlers

import asyncpg

from eevee.utils import snowflake

get_id = snowflake.create()

LOGGERS = ('eevee_logs', 'discord_logs')

module_logger = logging.getLogger('eevee.core.logger')

def init_logger(bot, debug_flag=False):

    # set root logger level
    logging.getLogger().setLevel(logging.DEBUG)

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
    bot.log_eevee_db = eevee_db
    eevee_log.addHandler(eevee_db)
    discord_db = DBLogHandler(bot, 'discord_logs')
    discord_log.addHandler(discord_db)

    bot.add_cog(ActivityLogging(bot))

    return eevee_log

class DBLogHandler(logging.Handler):
    def __init__(self, bot, log_name: str, level=logging.INFO):
        if log_name not in LOGGERS:
            raise RuntimeError(f'Unknown Log Name: {log_name}')
        self.bot = bot
        self.log_name = log_name
        self.logger = module_logger.getChild('DBLogHandler')
        super().__init__(level=level)

    def emit(self, record):
        record_id = next(get_id)
        asyncio.run_coroutine_threadsafe(
            self.submit_log(record_id, record), self.bot.loop)

    async def submit_log(self, log_id, record):
        data = dict(log_id=log_id, created=record.created,
                    logger_name=record.name, level_name=record.levelname,
                    file_path=record.pathname, module=record.module,
                    func_name=record.funcName, line_no=record.lineno,
                    message=record.message, traceback=record.exc_info)
        try:
            await self.bot.dbi.table(self.log_name).insert(**data)
        except asyncpg.PostgresError as e:
            self.logger.exception(type(e).__name__, exc_info=e)

class ActivityLogging:
    def __init__(self, bot):
        self.bot = bot
        self.logger = module_logger.getChild('ActivityLogging')

    async def on_message(self, msg):
        sent = int(msg.created_at.replace(tzinfo=timezone.utc).timestamp())
        guild_id = msg.guild.id if msg.guild else None
        embeds = [json.dumps(e.to_dict()) for e in msg.embeds]
        attachments = [a.url for a in msg.attachments]
        data = dict(message_id=msg.id, sent=sent, is_edit=False, deleted=False,
                    author_id=msg.author.id, channel_id=msg.channel.id,
                    guild_id=guild_id, content=msg.content,
                    clean_content=msg.clean_content, embeds=embeds,
                    webhook_id=msg.webhook_id, attachments=attachments)
        try:
            await self.bot.dbi.table('discord_messages').insert(**data)
        except asyncpg.PostgresError as e:
            self.logger.exception(type(e).__name__, exc_info=e)

    async def on_command(self, ctx):
        created = ctx.message.created_at
        sent = int(created.replace(tzinfo=timezone.utc).timestamp())
        guild = ctx.guild.id if ctx.guild else None
        cog = ctx.cog.__class__.__name__ if ctx.cog else None
        data = dict(message_id=ctx.message.id, sent=sent,
                    author_id=ctx.author.id, channel_id=ctx.channel.id,
                    guild_id=guild, prefix=ctx.prefix,
                    command=ctx.command.name, invoked_with=ctx.invoked_with,
                    invoked_subcommand=ctx.invoked_subcommand,
                    subcommand_passed=ctx.subcommand_passed,
                    command_failed=ctx.command_failed, cog=cog)
        try:
            await self.bot.dbi.table('command_log').insert(**data)
        except asyncpg.UniqueViolationError:
            pass
        except asyncpg.PostgresError as e:
            self.logger.exception(type(e).__name__, exc_info=e)

    async def on_member_update(self, before, after):
        status_update = None
        status_from = None
        name_update = None
        if before.status != after.status:
            status_update = str(after.status)
            status_from = str(before.status)
        if before.nick != after.nick:
            name_update = after.display_name
        if not status_update or name_update:
            return
        time_value = int(time.time())
        guild = after.guild.id if after.guild else None
        data = dict(member_id=after.id, time=time_value,
                    status=status_update, from_status=status_from,
                    guild_id=guild, display_name=name_update)
        try:
            await self.bot.dbi.table('member_activity').insert(**data)
        except asyncpg.UniqueViolationError:
            pass
        except asyncpg.PostgresError as e:
            self.logger.exception(type(e).__name__, exc_info=e)
