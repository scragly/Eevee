import inspect
import io
import os
import textwrap
import traceback
import unicodedata
import json
from datetime import datetime
from contextlib import redirect_stdout

import discord
from discord.ext import commands

from eevee import checks, command
from eevee.utils import make_embed
from eevee.utils.formatters import ilcode
from eevee.utils.converters import BotCommand, Guild, Multi


class Dev:
    """Developer Tools"""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.bot.config.command_categories['Developer'] = {
            "index" : "6",
            "description" : "Developer Tools"
        }

    def __local_check(self, ctx):
        return checks.check_is_co_owner(ctx)

    @command(category='Developer')
    async def charinfo(self, ctx, *, characters: str):
        """Shows you information about a number of characters.
        Only up to 25 characters at a time.
        """
        if len(characters) > 25:
            return await ctx.send(f'Too many characters ({len(characters)}/25)')
        embed = make_embed(msg_type='info')
        charlist = []
        rawlist = []
        for char in characters:
            digit = f'{ord(char):x}'
            url = f"http://www.fileformat.info/info/unicode/char/{digit}"
            name = f"[{unicodedata.name(char, '')}]({url})"
            u_code = f'\\U{digit:>08}'
            if len(f'{digit}') <= 4:
                u_code = f'\\u{digit:>04}'
            charlist.append(' '.join([ilcode(u_code.ljust(10)+':'), name, '-', char]))
            rawlist.append(u_code)
        embed.add_field(name='Character Info', value='\n'.join(charlist))
        if len(characters) > 1:
            embed.add_field(name='Raw', value=ilcode(''.join(rawlist)), inline=False)
        await ctx.send(embed=embed)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @command(category='Developer', name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = (f'async def func():\n{textwrap.indent(body, "  ")}')

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    paginator = commands.Paginator(prefix='```py')
                    for line in textwrap.wrap(value, 80):
                        paginator.add_line(line.rstrip().replace('`', '\u200b`'))
                    for p in paginator.pages:
                        await ctx.send(p)
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @command(category="Developer", name='print')
    async def _print(self, ctx, *, body: str):
        """Prints code snippets"""
        ctx.message.content = f'!eval print({body})'
        await ctx.bot.process_commands(ctx.message)

    @command(category="Developer")
    async def runas(self, ctx, member: discord.Member, *, new_cmd):
        """Run a command as a different member."""
        if await ctx.bot.is_owner(member):
            await ctx.send(embed=make_embed(
                msg_type='error', title='No, you may not run as owner.'))
            return
        ctx.message.content = new_cmd
        ctx.message.author = member
        await ctx.bot.process_commands(ctx.message)

    @command(category="Developer", aliases=['src'])
    @commands.cooldown(rate=2, per=5, type=commands.BucketType.user)
    async def source(self, ctx, *, command: BotCommand):
        """Displays the source code for a particular command.
        There is a per-user, 2 times per 5 seconds cooldown in order to prevent spam.
        """
        paginator = commands.Paginator(prefix='```py')
        for line in inspect.getsourcelines(command.callback)[0]:
            paginator.add_line(line.rstrip().replace('`', '\u200b`'))

        for p in paginator.pages:
            await ctx.send(p)

    @command(category="Developer")
    async def clear_console(self, ctx):
        """Clear the console"""
        os.system('cls')
        await ctx.ok()

    @command(category="Developer")
    async def guild(self, ctx, *, guild: Guild):
        """Lookup Guild info"""
        if guild:
            if guild.unavailable:
                embed = make_embed(
                    msg_type='error', title='Guild found, but unavailable!')
            else:
                embed = make_embed(
                    msg_type='info', thumbnail=guild.icon_url_as(format='png'))
                date_created = datetime.strftime(
                    guild.created_at, "UTC %Y/%m/%d %H:%M")
                basic_info = (
                    f"ID: {guild.id}\n"
                    f"Owner: {guild.owner}\n"
                    f"Created: {date_created}\n"
                    f"Region: {guild.region}\n")
                embed.add_field(
                    name=guild.name, value=basic_info, inline=False)
                stats_info = (
                    f"Members: {guild.member_count}\n"
                    f"Roles: {len(guild.roles)}\n"
                    f"Text Channels: {len(guild.text_channels)}\n"
                    f"Channel Categories: {len(guild.categories)}")
                embed.add_field(name='Stats', value=stats_info, inline=False)

                guild_perms = guild.me.guild_permissions
                req_perms = ctx.bot.req_perms
                perms_compare = guild_perms >= req_perms
                core_dir = ctx.bot.core_dir
                data_dir = os.path.join(core_dir, '..', 'data')
                data_file = 'permissions.json'
                perms_info = f"Value: {guild_perms.value}\n"
                perms_info += f"Meets Requirements: {perms_compare}\n"
                with open(os.path.join(data_dir, data_file), "r") as perm_json:
                    perm_dict = json.load(perm_json)

                for perm, bitshift in perm_dict.items():
                    if bool((req_perms.value >> bitshift) & 1):
                        if bool((guild_perms.value >> bitshift) & 1):
                            perms_info += ":white_small_square:  {}\n".format(perm)
                        else:
                            perms_info += ":black_small_square:  {}\n".format(perm)
                embed.add_field(name='Permissions', value=perms_info, inline=False)

                bot_list = [m for m in guild.members if m.bot]
                bot_info = f"Bots: {len(bot_list)}\n"
                if 1 <= len(bot_list) <= 20:
                    for bot in bot_list:
                        online = bot.status == discord.Status.online
                        status = "\U000025ab" if online else "\U000025aa"
                        bot_info += f"{status} {bot}\n"
                embed.add_field(name='Bots', value=bot_info, inline=False)

        else:
            embed = make_embed(msg_type='error', title='Guild not found')
        await ctx.send(embed=embed)

    @command(category="Developer", name='say')
    async def _say(self, ctx, *, msg):
        """Repeat the given message."""
        await ctx.send(msg)

    @command(category="Developer")
    async def emoji(self, ctx, emoji_id: int):
        """Sends a custom emoji by the given ID."""
        await ctx.send(f'<:emojitest:{emoji_id}>')

    @command(category="Developer")
    async def check_perms(
            self, ctx, member_or_role: Multi(discord.Member, discord.Role),
            guild_or_channel: Multi(
                discord.Guild, discord.TextChannel, discord.VoiceChannel)=None):
        """Show permissions of a member or role for the guild and channel."""
        if guild_or_channel:
            if isinstance(guild_or_channel, discord.Guild):
                guild_perms = ctx.guild.me.guild_permissions
        else:
            guild_perms = ctx.guild.me.guild_permissions
            if isinstance(member_or_role, discord.Member):
                chan_perms = ctx.channel.permissions_for(member_or_role)
            else:
                return await ctx.send("Role Permissions aren't done yet.")

        req_perms = ctx.bot.req_perms
        g_perms_compare = guild_perms >= req_perms
        c_perms_compare = chan_perms >= req_perms
        core_dir = ctx.bot.core_dir
        data_dir = os.path.join(core_dir, '..', 'data')
        data_file = 'permissions.json'
        msg = f"**Guild:**\n{ctx.guild}\nID {ctx.guild.id}\n"
        msg += f"**Channel:**\n{ctx.channel}\nID {ctx.channel.id}\n"
        msg += "```py\nGuild     | Channel\n"
        msg += "----------|----------\n"
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
                    title=f'Permissions for {member_or_role}',
                    content=msg)
                await ctx.send(embed=embed)
            else:
                await ctx.send(msg)
        except discord.errors.Forbidden:
            embed = make_embed(
                msg_type='info',
                title=f'Permissions for {member_or_role}',
                content=msg)
            await ctx.author.send(embed=embed)
