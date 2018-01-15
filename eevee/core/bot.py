import itertools
import os
import platform
from collections import Counter
from datetime import datetime

import pkg_resources
from dateutil.relativedelta import relativedelta

import discord
from discord.utils import cached_property
from discord.ext import commands

from eevee import config
from eevee.core.context import Context
from eevee.core.data_manager import DatabaseInterface, DataManager
from eevee.utils import ExitCodes, pagination, fuzzymatch


class Eevee(commands.Bot):

    def __init__(self, **kwargs):
        self.default_prefix = config.bot_prefix
        self.owner = config.bot_master
        self._shutdown_mode = ExitCodes.CRITICAL
        self.counter = Counter()
        self.core_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(self.core_dir, "..", "data")
        self.config = config
        self.token = config.bot_token
        self.req_perms = discord.Permissions(config.bot_permissions)
        self.co_owners = config.bot_coowners
        self.language = config.lang_bot
        self.pkmn_language = config.lang_pkmn
        self.preload_ext = config.preload_extensions
        self.dbi = DatabaseInterface(hostname=config.db_host,
                                     username=config.db_user,
                                     password=config.db_pass,
                                     database=config.db_name)
        self.data = DataManager(self.dbi)
        kwargs["command_prefix"] = self.dbi.prefix_manager
        kwargs["owner_id"] = self.owner
        kwargs["status"] = discord.Status.dnd
        super().__init__(**kwargs)
        self.loop.run_until_complete(self._db_connect())

    async def _db_connect(self):
        await self.dbi.start()

    async def send_cmd_help(self, ctx, **kwargs):
        try:
            if ctx.invoked_subcommand:
                kwargs['title'] = kwargs.get('title', 'Sub-Command Help')
                p = await pagination.Pagination.from_command(
                    ctx, ctx.invoked_subcommand, **kwargs)
            else:
                kwargs['title'] = kwargs.get('title', 'Command Help')
                p = await pagination.Pagination.from_command(
                    ctx, ctx.command, **kwargs)
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
        await self.dbi.stop()
        await self.logout()

    @cached_property
    def invite_url(self):
        invite_url = discord.utils.oauth_url(self.user.id,
                                             permissions=self.req_perms)
        return invite_url

    @property
    def avatar(self):
        return self.user.avatar_url_as(static_format='png')

    @property
    def avatar_small(self):
        return self.user.avatar_url_as(static_format='png', size=64)

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

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=Context)

        if not ctx.command:
            return

        await self.invoke(ctx)

    def match(self, data_list, item):
        result = fuzzymatch.get_match(data_list, item)[0]
        if not result:
            return None
        return result

    def get(self, iterable, **attrs):
        """A helper that returns the first element in an iterable that meets
        all the attributes passed in `attrs`.
        """
        return discord.utils.get(iterable, **attrs)

    def find_guild(self, name):
        """A helper that searches for a channel by name."""
        result = self.get(self.guilds, name=name)
        if not result:
            guild_list = (guild.name for guild in self.guilds)
            result = self.match(guild_list, name)
            if not result:
                return None
            else:
                result = self.get(self.guilds, name=result)
        return result

    @cached_property
    def version(self):
        return pkg_resources.get_distribution("eevee").version

    @cached_property
    def py_version(self):
        return platform.python_version()

    @cached_property
    def dpy_version(self):
        return pkg_resources.get_distribution("discord.py").version

    @cached_property
    def platform(self):
        return platform.platform()

    # events
    async def on_message(self, message):
        self.counter["messages_read"] += 1
        await self.process_commands(message)

    async def on_resumed(self):
        self.counter["sessions_resumed"] += 1

    async def on_command(self, ctx):
        self.counter["received_commands"] += 1

    async def on_command_completion(self, ctx):
        self.counter["processed_commands"] += 1

    async def on_connect(self):
        if hasattr(self, 'launch_time'):
            print("Reconnected.")
        else:
            await self.change_presence(status=discord.Status.idle)

    async def on_ready(self):
        intro = "Eevee - Pokemon Go Bot for Discord"
        intro_deco = "{0}\n{1}\n{0}".format('='*len(intro), intro)
        if not hasattr(self, 'launch_time'):
            self.launch_time = datetime.utcnow()
            await self.change_presence(status=discord.Status.online)
        if not self.launcher:
            print(intro_deco)
        print("We're on!\n")
        print(f"Eevee Version: {self.version}\n")
        if self.debug:
            print(f"Python Version: {self.py_version}")
            print(f"Discord.py Version: {self.dpy_version}")
            print(f"Platform: {self.platform}\n")
        guilds = len(self.guilds)
        users = len(list(self.get_all_members()))
        if guilds:
            print(f"Servers: {guilds}")
            print(f"Members: {users}")
        else:
            print("I'm not in any server yet, so be sure to invite me!")
        if self.invite_url:
            print(f"\nInvite URL: {self.invite_url}\n")

# command decorators

def command(*args, **kwargs):
    """A decorator that adds a function as a bot command.

    Attributes
    -----------
    name: :class:`str`
        The name of the command.
    help: :class:`str`
        The details in command help.
    aliases: :class:`list`
        The list of other command names this will work with.
    enabled: :class:`bool`
        If ``False`` the command is disabled and will raise
        :exc:`discord.ext.commands.DisabledCommand`.
    description: :class:`str`
        An added message placed before help text in command help.
    hidden: :class:`bool`
        If ``True`` the command won't show in help command lists.
    ignore_extra: :class:`bool`
        If ``False`` any extra arguments raise
        :exc:`discord.ext.commands.TooManyArguments`.
    """
    def decorator(func):
        category = kwargs.get("category")
        func.command_category = category
        result = commands.command(*args, **kwargs)(func)
        return result
    return decorator

def group(*args, **kwargs):
    """A decorator that adds a function as a bot command group.

    These allow for easy subcommands using `funcname.command()`.

    Attributes
    -----------
    name: :class:`str`
        The name of the command.
    help: :class:`str`
        The details in command help.
    aliases: :class:`list`
        The list of other command names this will work with.
    enabled: :class:`bool`
        If ``False`` the command is disabled and will raise
        :exc:`discord.ext.commands.DisabledCommand`.
    description: :class:`str`
        An added message placed before help text in command help.
    hidden: :class:`bool`
        If ``True`` the command won't show in help command lists.
    ignore_extra: :class:`bool`
        If ``False`` any extra arguments raise
        :exc:`discord.ext.commands.TooManyArguments`.
    invoke_without_command: :class:`bool`
        If ``True``, invoked subcommands will skip the group commands
        checks and argument parsing, instead moving directly to the sub.
    """
    def decorator(func):
        category = kwargs.get("category")
        func.command_category = category
        result = commands.group(*args, **kwargs)(func)
        return result
    return decorator
