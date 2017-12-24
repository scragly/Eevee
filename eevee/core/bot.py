import os
import itertools
from collections import Counter
from datetime import datetime

from dateutil.relativedelta import relativedelta

import discord
from discord.ext import commands

from eevee import config
from eevee.utils import ExitCodes, pagination
from eevee.core.data_manager import DatabaseInterface, DataManager

class Eevee(commands.Bot):

    def __init__(self, **kwargs):
        self.default_prefix = config.bot_prefix
        self.owner = config.bot_master
        self._shutdown_mode = ExitCodes.CRITICAL
        self.counter = Counter()
        self.core_dir = os.path.dirname(os.path.realpath(__file__))
        self.config = config
        self.token = config.bot_token
        self.req_perms = discord.Permissions(config.bot_permissions)
        self.co_owners = config.bot_coowners
        self.language = config.lang_bot
        self.pkmn_language = config.lang_pkmn
        self.preload_ext = config.preload_extensions
        self.db = DatabaseInterface(hostname=config.db_host,
                                    username=config.db_user,
                                    password=config.db_pass,
                                    database=config.db_name)
        self.data = DataManager(self.db)
        kwargs["command_prefix"] = self.db.prefix_manager
        kwargs["owner_id"] = self.owner
        super().__init__(**kwargs)
        self.loop.run_until_complete(self._db_connect())

    async def _db_connect(self):
        await self.db.start()

    async def send_cmd_help(self, ctx):
        try:
            if ctx.invoked_subcommand:
                p = await pagination.Pagination.from_command(
                    ctx, ctx.invoked_subcommand)
            else:
                p = await pagination.Pagination.from_command(ctx, ctx.command)
            await p.paginate()
        except Exception as e:
            await ctx.send(e)

    async def shutdown(self, *, restart=False):
        """Shutdown the bot.

        Safely ends the bot connection while passing the exit code based
        on if the intention was to restart or close.
        """
        if not restart:
            self._shutdown_mode = ExitCodes.SHUTDOWN
        else:
            self._shutdown_mode = ExitCodes.RESTART
        await self.db.stop()
        await self.logout()

    @discord.utils.cached_property
    def invite_url(self):
        invite_url = discord.utils.oauth_url(self.user.id,
                                             permissions=self.req_perms)
        return invite_url

    @property
    def uptime(self):
        return relativedelta(datetime.utcnow(), self.launch_time)

    @property
    def uptime_str(self):
        uptime = self.uptime
        year_str, month_str, day_str, hour_str = ('',)*4
        if uptime.years >= 1:
            year_str = "{0}y ".format(uptime.years)
        if uptime.months >= 1 or year_str:
            month_str = "{0}m ".format(uptime.months)
        if uptime.days >= 1 or month_str:
            d_unit = 'd' if month_str else ' days'
            day_str = "{0}{1} ".format(uptime.days, d_unit)
        if uptime.hours >= 1 or day_str:
            h_unit = ':' if month_str else ' hrs'
            hour_str = "{0}{1}".format(uptime.hours, h_unit)
        m_unit = '' if month_str else ' mins'
        mins = uptime.minutes if month_str else ' {0}'.format(uptime.minutes)
        secs = '' if day_str else ' {0} secs'.format(uptime.seconds)
        min_str = "{0}{1}{2}".format(mins, m_unit, secs)

        uptime_str = ''.join((year_str, month_str, day_str, hour_str, min_str))

        return uptime_str

    @property
    def command_count(self):
        return self.counter["processed_commands"]

    @property
    def message_count(self):
        return self.counter["messages_read"]

    @property
    def resumed_count(self):
        return self.counter["sessions_resumed"]

    def get_category(self, category):
        def sortkey(cmd):
            categories = self.config.command_categories
            category = getattr(cmd.callback, 'command_category', None)
            cat_cfg = categories.get(category)
            category = cat_cfg["index"] if cat_cfg else category
            return category or '\u200b'
        def groupkey(cmd):
            category = getattr(cmd.callback, 'command_category', None)
            return category or '\u200b'
        entries = sorted(self.commands, key=sortkey)
        categories = []
        for cmd_group, _ in itertools.groupby(entries, key=groupkey):
            if cmd_group != '\u200b':
                categories.append(cmd_group)
        return category if category in categories else None

# command decorators

def command(*args, **kwargs):
    def decorator(func):
        category = kwargs.get("category")
        func.command_category = category
        result = commands.command(*args, **kwargs)(func)
        return result
    return decorator

def group(*args, **kwargs):
    def decorator(func):
        category = kwargs.get("category")
        func.command_category = category
        result = commands.group(*args, **kwargs)(func)
        return result
    return decorator
