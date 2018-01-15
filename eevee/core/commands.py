import asyncio
import json
import os

import aiohttp
import psutil

import discord
from discord.ext import commands

from eevee import command, group, checks
from eevee.utils.pagination import Pagination
from eevee.utils.formatters import url_color, make_embed

class Core:
    """General bot functions."""

    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    @command(name="shutdown", aliases=["exit"], category='Owner')
    @checks.is_owner()
    async def _shutdown(self, ctx):
        """Shuts down the bot"""
        embed = make_embed(
            title='Shutting down.',
            msg_colour='red',
            icon="https://i.imgur.com/uBYS8DR.png")
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            pass
        await ctx.bot.shutdown()

    @command(name="break", category='Owner')
    @checks.is_owner()
    async def _break(self, ctx):
        """Simulates a sudden disconnection."""
        embed = make_embed(msg_type='warning', title='Faking a crash...')
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            pass
        await ctx.bot.logout()

    @command(name="restart", category='Owner')
    @checks.is_owner()
    async def _restart(self, ctx):
        """Restarts the bot"""
        embed = make_embed(
            title='Restarting.',
            msg_colour='red',
            icon="https://i.imgur.com/uBYS8DR.png")
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            pass
        await ctx.bot.shutdown(restart=True)

    @group(name="set", category='Owner')
    @checks.is_co_owner()
    async def _set(self, ctx):
        """Changes Eevee's settings"""
        if ctx.invoked_subcommand is None:
            await ctx.bot.send_cmd_help(ctx)

    @_set.command(name="game")
    @checks.is_co_owner()
    async def _game(self, ctx, *, game: str):
        """Sets Eevee's game status"""
        status = ctx.me.status
        game = discord.Game(name=game)
        await ctx.bot.change_presence(status=status, game=game)
        embed = make_embed(msg_type='success', title='Game set.')
        await ctx.send(embed=embed)

    @_set.command()
    @checks.is_co_owner()
    async def status(self, ctx, *, status: str):
        """Sets Eevee's status
        Available statuses:
            online
            idle
            dnd
        """

        statuses = {
            "online"    : discord.Status.online,
            "idle"      : discord.Status.idle,
            "dnd"       : discord.Status.dnd,
            "invisible" : discord.Status.invisible
            }

        game = ctx.me.game

        try:
            status = statuses[status.lower()]
        except KeyError:
            await ctx.bot.send_cmd_help(ctx)
        else:
            await ctx.bot.change_presence(status=status,
                                          game=game)
            embed = make_embed(
                msg_type='success',
                title="Status changed to {}.".format(status))
            await ctx.send(embed=embed)

    @_set.command(name="username", aliases=["name"])
    @checks.is_owner()
    async def _username(self, ctx, *, username: str):
        """Sets Eevee's username"""
        try:
            await ctx.bot.user.edit(username=username)
        except discord.HTTPException:
            embed = make_embed(
                msg_type='error',
                title="Failed to change name",
                content=("Remember that you can only do it up to 2 times an "
                         "hour. Use nicknames if you need frequent changes. "
                         "**{}set nickname**").format(ctx.prefix))
            await ctx.send(embed=embed)
        else:
            embed = make_embed(msg_type='success', title="Username set.")
            await ctx.send(embed=embed)

    @_set.command(name="avatar")
    @checks.is_co_owner()
    async def _avatar(self, ctx, *, avatar_url: str):
        """Sets Eevee's avatar"""
        session = aiohttp.ClientSession()
        async with session.get(avatar_url) as req:
            data = await req.read()
        await session.close()
        try:
            await ctx.bot.user.edit(avatar=data)
        except discord.HTTPException:
            embed = make_embed(
                msg_type='error',
                title="Failed to set avatar",
                content=("Remember that you can only do it up to 2 "
                         "times an hour. URL must be a direct link to "
                         "a JPG / PNG."))
            await ctx.send(embed=embed)
        else:
            embed = make_embed(msg_type='success', title="Avatar set.")
            await ctx.send(embed=embed)

    @_set.command(name="nickname")
    @checks.is_admin()
    @commands.guild_only()
    async def _nickname(self, ctx, *, nickname: str):
        """Sets Eevee's nickname"""
        try:
            await ctx.guild.me.edit(nick=nickname)
        except discord.Forbidden:
            embed = make_embed(
                msg_type='error',
                title="Failed to set nickname",
                content=("I'm missing permissions to change my nickname. "
                         "Use **{}get guildperms** to check permissions."
                         "").format(ctx.prefix))
            await ctx.send()
        else:
            embed = make_embed(msg_type='success', title="Nickname set.")
            await ctx.send(embed=embed)

    @command(name="uptime", category='Bot Info')
    async def _uptime(self, ctx):
        """Shows Eevee's uptime"""
        uptime_str = ctx.bot.uptime_str
        embed = make_embed(
            title='Uptime',
            content=uptime_str,
            msg_colour='blue',
            icon="https://i.imgur.com/82Cqf1x.png")
        try:
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            await ctx.send("Uptime: {}".format(uptime_str))

    @command(name="botinvite", category='Bot Info')
    async def _bot_invite(self, ctx, plain_url: bool = False):
        """Shows Eevee's invite url"""
        invite_url = ctx.bot.invite_url
        if plain_url:
            await ctx.send("Invite URL: <{}>".format(invite_url))
            return
        else:
            embed = make_embed(
                title='Click to invite me to your server!',
                title_url=invite_url,
                msg_colour='blue',
                icon="https://i.imgur.com/DtPWJPG.png")
        try:
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            await ctx.send("Invite URL: <{}>".format(invite_url))

    @command(name="about", category='Bot Info')
    async def _about(self, ctx):
        """Shows info about Eevee"""
        bot = ctx.bot
        author_repo = "https://github.com/scragly"
        bot_repo = author_repo + "/Eevee"
        server_url = "https://discord.gg/hhVjAN8"
        owner = await bot.get_user_info(ctx.bot.owner)
        uptime_str = bot.uptime_str
        invite_str = ("[Click to invite me to your server!]({})"
                      "").format(bot.invite_url)

        about = (
            "I help organise and coordinate Pokemon Go trainers!\n"
            "[Check out my code and docs!]({bot_repo})\n\n"
            "").format(bot_repo=bot_repo)

        member_count = 0
        server_count = 0
        for guild in bot.guilds:
            server_count += 1
            member_count += guild.member_count

        embed_colour = await url_color(bot.avatar_small)
        embed = make_embed(
            icon=bot.avatar_small, title=f"{bot.user}",
            content=about, msg_colour=embed_colour)
        embed.set_thumbnail(url=bot.avatar)
        embed.add_field(name="Owner", value=owner)
        embed.add_field(name="Uptime", value=uptime_str)
        embed.add_field(name="Servers", value=server_count)
        embed.add_field(name="Members", value=member_count)
        embed.add_field(name="Version", value=bot.version)
        embed.add_field(name="D.Py Version", value=bot.dpy_version)
        embed.add_field(name="Invite Link", value=invite_str, inline=False)
        footer_txt = ("For support, contact us on our Discord server. "
                      "Invite Code: hhVjAN8")
        embed.set_footer(text=footer_txt)

        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    def get_cpu(self):
        return psutil.cpu_percent(interval=1)

    @command(name="stats", category='Owner')
    @checks.is_co_owner()
    async def _stats(self, ctx):
        """Shows stats about Eevee"""
        bot = ctx.bot
        owner = await bot.get_user_info(ctx.bot.owner)
        uptime_str = bot.uptime_str
        cpu_p = await ctx.bot.loop.run_in_executor(None, self.get_cpu)
        mem = psutil.virtual_memory()
        mem_p = round((mem.available / mem.total) * 100, 2)
        bot_process = psutil.Process()
        ppid = bot_process.ppid()
        p_user = bot_process.username()
        p_mem = bot_process.memory_info().rss
        swapped = psutil.swap_memory().used

        data_sizes = {
            'B':1,
            'KB':1024,
            'MB':1048576,
            'GB':1073741824
        }
        for size, value in data_sizes.items():
            if (p_mem / value) > 1 < 1024:
                p_mem_str = "{} {}".format(
                    round(p_mem / value, 2), size)
            if (swapped / value) > 1 < 1024:
                swap_str = "{} {}".format(
                    round(swapped / value, 2), size)

        member_count = 0
        server_count = 0
        for guild in bot.guilds:
            server_count += 1
            member_count += guild.member_count

        embed = make_embed(
            msg_type='info', title="Eevee Statistics")
        instance_msg = (
            f"**Owner:** {owner}\n**Uptime:** {uptime_str}\n"
            f"**Version:** {bot.version}\n"
            f"**D.Py Ver:** {bot.dpy_version}\n"
            f"**Python:** {bot.py_version}")
        session_msg = (
            f"**Servers:** {server_count}\n**Members:** {member_count}\n"
            f"**Messages:** {bot.message_count}\n"
            f"**Commands:** {bot.command_count}\n"
            f"**Reconnections:** {bot.resumed_count}")
        process_msg = (
            f"**PID:** {ppid}\n**Process RAM:** {p_mem_str}\n"
            f"**Swap File:** {swap_str}\n**System RAM:** {mem_p}\n"
            f"**System CPU:** {cpu_p}\n")
        embed.add_field(name="SESSION", value=session_msg)
        embed.add_field(name="PROCESS", value=process_msg)
        embed.add_field(name="INSTANCE", value=instance_msg)
        # cpm = bot.message_count/(bot.uptime.seconds+(bot.uptime.minutes*60))
        # activity_msg = (
        #     f"**Commands/min:** {cpm:.2f}\n"
        #     f"**Active Raids:** {0}\n")
        # embed.add_field(name="ACTIVITY", value=activity_msg)

        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    @group(name="get", category="Owner")
    @checks.is_co_owner()
    async def _get(self, ctx):
        """Gets Eevee's settings"""
        if ctx.invoked_subcommand is None:
            await ctx.bot.send_cmd_help(ctx)

    @group(category="Bot Info", name='permissions',
           aliases=['perms'], invoke_without_command='True')
    @checks.is_mod()
    async def bot_perms(self, ctx):
        """Show Eevee's permissions for the guild and channel."""
        guild_perms = ctx.guild.me.guild_permissions
        chan_perms = ctx.channel.permissions_for(ctx.guild.me)
        req_perms = ctx.bot.req_perms
        g_perms_compare = guild_perms >= req_perms
        c_perms_compare = chan_perms >= req_perms
        core_dir = ctx.bot.core_dir
        data_dir = os.path.join(core_dir, '..', 'data')
        data_file = 'permissions.json'
        msg = f"**Guild:**\n{ctx.guild}\nID {ctx.guild.id}\n"
        msg += f"**Channel:**\n{ctx.channel}\nID {ctx.channel.id}\n"
        msg += "```py\nGuild     | Channel\n"
        msg +=   "----------|----------\n"
        msg += "{} | {}\n".format(guild_perms.value, chan_perms.value)
        msg += "{0:9} | {1}```".format(str(g_perms_compare), str(c_perms_compare))
        y_emj = ":white_small_square:"
        n_emj = ":black_small_square:"

        with open(os.path.join(data_dir, data_file), "r") as perm_json:
            perm_dict = json.load(perm_json)

        for perm, bitshift in perm_dict.items():
            if bool((req_perms.value >> bitshift) & 1):
                guild_bool = bool((guild_perms.value >> bitshift) & 1)
                channel_bool = bool((chan_perms.value >> bitshift) & 1)
                guild_e = y_emj if guild_bool else n_emj
                channel_e = y_emj if channel_bool else n_emj
                msg += f"{guild_e} {channel_e}  {perm}\n"

        try:
            if chan_perms.embed_links:
                embed = make_embed(
                    msg_type='info',
                    title='Bot Permissions',
                    content=msg)
                await ctx.send(embed=embed)
            else:
                await ctx.send(msg)
        except discord.errors.Forbidden:
            embed = make_embed(
                msg_type='info',
                title='Guild Permissions',
                content=msg)
            await ctx.author.send(embed=embed)

    @bot_perms.command(name='guild')
    @checks.is_mod()
    async def guild_perms(self, ctx, guild_id=None):
        """Gets Eevee's permissions for the guild."""
        if not ctx.guild and not guild_id:
            await ctx.send(embed=make_embed(
                msg_type='error', title="This is a DM. Please provide ID."))
            return
        if guild_id:
            guild = ctx.bot.get_guild(int(guild_id))
            if not guild:
                await ctx.send(embed=make_embed(
                    msg_type='error', title="Guild not found"))
                return
        else:
            guild = ctx.guild

        guild_perms = guild.me.guild_permissions
        req_perms = ctx.bot.req_perms
        perms_compare = guild_perms >= req_perms
        core_dir = ctx.bot.core_dir
        data_dir = os.path.join(core_dir, '..', 'data')
        data_file = 'permissions.json'
        msg = f"{guild}\nID {guild.id}\n"
        msg += f"```py\n{guild_perms.value}\n"
        msg += f"{perms_compare}```"

        with open(os.path.join(data_dir, data_file), "r") as perm_json:
            perm_dict = json.load(perm_json)

        for perm, bitshift in perm_dict.items():
            if bool((req_perms.value >> bitshift) & 1):
                if bool((guild_perms.value >> bitshift) & 1):
                    msg += ":white_small_square:  {}\n".format(perm)
                else:
                    msg += ":black_small_square:  {}\n".format(perm)

        try:
            if not isinstance(ctx.channel, discord.DMChannel):
                if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
                    await ctx.send(msg)
                    return
            embed = make_embed(
                msg_type='info',
                title='Guild Permissions',
                content=msg)
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            embed = make_embed(
                msg_type='info',
                title='Guild Permissions',
                content=msg)
            await ctx.author.send(embed=embed)

    @bot_perms.command(name='channel', aliases=['chan'])
    @checks.is_mod()
    async def channel_perms(self, ctx, channel_id=None):
        """Gets Eevee's permissions for the channel."""
        if channel_id:
            channel = ctx.bot.get_channel(int(channel_id))
            if not channel:
                await ctx.send(embed=make_embed(
                    msg_type='error', title="Channel not found"))
                return
        else:
            channel = ctx.channel

        dm_channel = isinstance(channel, discord.DMChannel)
        me = ctx.bot.user if dm_channel else channel.guild.me
        chan_perms = channel.permissions_for(me)
        req_perms = ctx.bot.req_perms
        perms_compare = chan_perms >= req_perms
        core_dir = ctx.bot.core_dir
        data_dir = os.path.join(core_dir, '..', 'data')
        data_file = 'permissions.json'
        msg = ""
        if not dm_channel:
            msg += f"{channel.guild}\nID {channel.guild.id}\n"
        msg += f"{channel}\nID {channel.id}\n"
        msg += f"```py\n{chan_perms.value}\n"
        msg += f"{perms_compare}```"

        with open(os.path.join(data_dir, data_file), "r") as perm_json:
            perm_dict = json.load(perm_json)

        for perm, bitshift in perm_dict.items():
            if bool((req_perms.value >> bitshift) & 1):
                if bool((chan_perms.value >> bitshift) & 1):
                    msg += f":white_small_square:  {perm}\n"
                else:
                    msg += f":black_small_square:  {perm}\n"
        try:
            if not isinstance(ctx.channel, discord.DMChannel):
                if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
                    await ctx.send(msg)
                    return
            embed = make_embed(
                msg_type='info',
                title='Channel Permissions',
                content=msg)
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            embed = make_embed(
                msg_type='info',
                title='Channel Permissions',
                content=msg)
            await ctx.author.send(embed=embed)

    @command(name="resumed", category='Bot Info')
    async def _resumed(self, ctx):
        """Gets the number of websocket reconnections."""
        r_c = ctx.bot.resumed_count
        embed = make_embed(msg_type='info',
                           title=f"Connections Resumed: {r_c}")
        await ctx.send(embed=embed)

    @command(name="ping", category='Bot Info')
    async def _ping(self, ctx):
        msg = ("{0:.2f} ms").format(ctx.bot.ws.latency * 1000)
        embed = make_embed(msg_type='info', title=f'Bot Latency: {msg}')
        await ctx.send(embed=embed)

    @command(category='Owner')
    @checks.is_admin()
    async def purge(self, ctx, msg_number: int = 10):
        """Delete a number of messages from the channel.

        Default is 10. Max 100."""
        if msg_number > 100:
            embed = make_embed(
                msg_type='info',
                title="ERROR",
                content="No more than 100 messages can be purged at a time.",
                guild=ctx.guild)
            await ctx.send(embed=embed)
            return
        deleted = await ctx.channel.purge(limit=msg_number)
        embed = make_embed(
            msg_type='success',
            title='Deleted {} message{}'.format(
            len(deleted), "s" if len(deleted) > 1 else ""))
        result_msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await result_msg.delete()

    @command(category='Owner')
    @checks.is_co_owner()
    async def reload_cm(self, ctx):
        """Reload Cog Manager."""
        bot = ctx.bot
        try:
            bot.unload_extension('eevee.core.cog_manager')
            bot.load_extension('eevee.core.cog_manager')
            embed = make_embed(msg_type='success',
                               title='Cog Manager reloaded.')
            await ctx.send(embed=embed)
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            embed = make_embed(msg_type='error',
                               title='Error loading Cog Manager',
                               content=msg)
            await ctx.send(embed=embed)

    @command(name="prefix", category='Bot Info')
    async def _prefix(self, ctx, *, new_prefix: str = None):
        """Get and set server prefix.
        Use the argument 'reset' to reset the guild prefix to default.
        """
        bot = ctx.bot
        default_prefix = bot.default_prefix
        if ctx.guild:
            if new_prefix:
                await bot.data.guild(ctx.guild.id).prefix(new_prefix)
                if new_prefix.lower() == 'reset':
                    new_prefix = bot.default_prefix
                embed = make_embed(
                    msg_type='success', title=f"Prefix set to {new_prefix}")
                await ctx.send(embed=embed)
            else:
                guild_prefix = await bot.data.guild(ctx.guild).prefix()
                prefix = guild_prefix if guild_prefix else default_prefix
                if len(prefix) > 1:
                    prefix = ', '.join(default_prefix)
                else:
                    prefix = prefix[0]
                embed = make_embed(
                    msg_type='info', title=f"Prefix is {prefix}")
                await ctx.send(embed=embed)
        else:
            if len(default_prefix) > 1:
                prefix = ', '.join(default_prefix)
            else:
                prefix = default_prefix[0]
            embed = make_embed(
                msg_type='info', title=f"Prefix is {prefix}")
            await ctx.send(embed=embed)

    @command(name='help', category='Bot Info')
    async def _help(self, ctx, *, command: str = None):
        """Shows help on available commands."""
        try:
            if command is None:
                p = await Pagination.from_bot(ctx)
            else:
                entity = (self.bot.get_category(command) or
                          self.bot.get_cog(command) or
                          self.bot.get_command(command))
                if entity is None:
                    clean = command.replace('@', '@\u200b')
                    return await ctx.send(f'Command or category "{clean}" not found.')
                elif isinstance(entity, commands.Command):
                    p = await Pagination.from_command(ctx, entity)
                elif isinstance(entity, str):
                    p = await Pagination.from_category(ctx, entity)
                else:
                    p = await Pagination.from_cog(ctx, entity)

            await p.paginate()
        except Exception as e:
            await ctx.send(e)

def setup(bot):
    bot.add_cog(Core(bot))
