import asyncio

import discord
from discord.abc import Messageable
from discord.ext import commands

from eevee.core import checks
from eevee.utils.formatters import convert_to_bool, make_embed


class GetTools:
    def __init__(self, ctx):
        self.ctx = ctx
        self.get = discord.utils.get

    def channel(self, id=None, name=None):
        guild = self.ctx.guild
        if not guild:
            return None
        if id:
            return guild.get_channel(id)
        if name:
            return self.get(guild.channels, name=name)

    def text_channel(self, id=None, name=None):
        guild = self.ctx.guild
        if not guild:
            return None
        if id:
            channel = guild.get_channel(id)
            if isinstance(channel, discord.TextChannel):
                return channel
            return None
        if name:
            return self.get(guild.text_channels, name=name)

    def id(self, voice_channel_id=None, name=None):
        guild = self.ctx.guild
        if not guild:
            return None
        if id:
            channel = guild.get_channel(id)
            if isinstance(channel, discord.VoiceChannel):
                return channel
            return None
        if name:
            return self.get(guild.voice_channels, name=name)

    def category(self, id=None, name=None):
        guild = self.ctx.guild
        if not guild:
            return None
        if id:
            channel = guild.get_channel(id)
            if isinstance(channel, discord.CategoryChannel):
                return channel
            return None
        if name:
            return self.get(guild.categories, name=name)

    def member(self, id=None, name=None):
        guild = self.ctx.guild
        if not guild:
            return None
        if id:
            return guild.get_member(id)
        if name:
            member = self.get(guild.members, name=name)
            if not member:
                member = self.get(guild.members, nick=name)
            if not member:
                members = {str(m) : m for m in guild.members}
                member = members.get(name, None)
            return member

    def role(self, id=None, name=None):
        guild = self.ctx.guild
        if not guild:
            return None
        if id:
            return self.get(guild.roles, id=id)
        if name:
            return self.get(guild.roles, name=name)

    def guild(self, id=None, name=None):
        bot = self.ctx.bot
        if id:
            return bot.get_guild(id)
        if name:
            return self.get(bot.guilds, name=name)

    def emoji(self, id=None, name=None):
        bot = self.ctx.bot
        if id:
            return bot.get_emoji(id)
        if name:
            return self.get(bot.emojis, name=name)

class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dbi = self.bot.dbi
        self.data = self.bot.data
        if self.guild:
            self.guild_dm = self.bot.data.guild(self.guild.id)
            self.setting = self.guild_dm.settings
        self.get = GetTools(self)

    async def is_co_owner(self):
        return await checks.check_is_co_owner(self)

    @property
    def cog_name(self):
        return self.command.instance.__class__.__name__

    async def admin_role(self):
        role_id = await self.setting('AdminRole')
        role = discord.utils.get(self.guild.roles, id=int(role_id))
        return role

    async def mod_role(self):
        role_id = await self.setting('ModRole')
        role = discord.utils.get(self.guild.roles, id=int(role_id))
        return role

    async def cog_enabled(self, value: bool = None, *, clear=False):
        if clear:
            return await self.setting(self.cog_name+'Enabled', delete=True)
        elif value is not None:
            return await self.setting(self.cog_name+'Enabled', value)
        else:
            value = await self.setting(self.cog_name+'Enabled')
            if value is not None:
                value = convert_to_bool(value)
            return value

    async def error(self, title, details=None, log_level='warning',
                    exc: Exception = None):
        """Submit an error to log and reply with error message"""
        msg = await self.embed(
            title=title, description=details, msg_type='error')
        if exc:
            raise exc(details)
        else:
            log = getattr(self.bot.logger, log_level, 'warning')
            log_msg = f"Error in command '{self.command}': {title}"
            if details:
                log_msg += f" - {details}"
            log(log_msg)
        return msg

    async def info(self, title, details=None, send=True):
        """Quick send or build an info embed response."""
        return await self.embed(title, details, msg_type='info', send=send)

    async def embed(self, title, description=None, plain_msg='', *,
                    msg_type=None, title_url=None, colour=None,
                    icon=None, thumbnail='', image='', fields: dict = None,
                    footer=None, footer_icon=None, send=True):
        """Send or build an embed using context details."""
        embed = make_embed(title=title, content=description, msg_type=msg_type,
                           title_url=title_url, msg_colour=colour, icon=icon,
                           thumbnail=thumbnail, image=image, guild=self.guild)
        if fields:
            for key, value in fields.items():
                embed.add_field(name=key, value=value, inline=False)
        if footer:
            footer = {'text':footer}
            if footer_icon:
                footer['icon_url'] = footer_icon
            embed.set_footer(**footer)

        if not send:
            return embed

        return await self.send(plain_msg, embed=embed)

    async def ask(self, message, *, timeout: float = 30.0,
                  autodelete: bool = True, options: list = None,
                  author_id: int = None, destination: Messageable = None,
                  react_dict: dict = None):
        """An interactive reaction confirmation dialog.

        Parameters
        -----------
        message: Union[str, discord.Embed]
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning. Default is 30.
        autodelete: bool
            Whether to delete the confirmation message after we're done.
            Default is True.
        options: Optional[list]
            What react options are valid, limited to react_dict keys.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author of the
            Context's message.
        destination: Optional[discord.abc.Messageable]
            Where the prompt should be sent. Defaults to invoked channel.
        react_dict: Optional[dict]
            Custom react dict. Overrides existing one.

        Returns
        --------
        Optional[Union[bool, str, int]]
            ``1-5`` if selected numbered option,
            ``A-E`` if selected lettered option,
            ``True`` if confirm,
            ``False`` if deny,
            ``None`` if timeout

        If a custom react_dict is provide, it overrides default.
        """
        custom_reacts = bool(react_dict)
        if not custom_reacts:
            cek = '\u20e3'
            react_dict = {
                "1" : {
                    "emoji":"1"+cek,
                    "value":1
                },
                "2" : {
                    "emoji":"2"+cek,
                    "value":2
                },
                "3" : {
                    "emoji":"3"+cek,
                    "value":3
                },
                "4" : {
                    "emoji":"4"+cek,
                    "value":4
                },
                "5" : {
                    "emoji":"5"+cek,
                    "value":5
                },
                "a" : {
                    "emoji":"\U0001f1e6",
                    "value":"a"
                },
                "b" : {
                    "emoji":"\U0001f1e7",
                    "value":"b"
                },
                "c" : {
                    "emoji":"\U0001f1e8",
                    "value":"c"
                },
                "d" : {
                    "emoji":"\U0001f1e9",
                    "value":"d"
                },
                "e" : {
                    "emoji":"\U0001f1ea",
                    "value":"e"
                },
                "true" : {
                    "emoji":"\u2705",
                    "value":True
                },
                "false" : {
                    "emoji":"\u274e",
                    "value":False
                },
                "cancel" : {
                    "emoji":"\U0001f6ab",
                    "value":None
                },
            }

        destination = destination or self.channel

        emoji_list = []
        emoji_lookup = {}
        for key, item in react_dict.items():
            if not options and not custom_reacts:
                options = ['true', 'false']
            if options:
                if key not in options:
                    continue
            emoji_lookup[item['emoji']] = item['value']
            emoji_list.append(item['emoji'])

        is_valid_emoji = frozenset(emoji_list).__contains__

        if isinstance(message, discord.Embed):
            msg = await destination.send(embed=message)
        else:
            msg = await destination.send(message)

        author_id = author_id or self.author.id

        def check(emoji, message_id, channel_id, user_id):
            if message_id != msg.id or user_id != author_id:
                return False
            return is_valid_emoji(str(emoji))

        for emoji in emoji_list:
            # str cast in case of _ProxyEmoji
            if not isinstance(emoji, discord.Emoji):
                emoji = str(emoji)
            await msg.add_reaction(emoji)

        try:
            emoji, *_, = await self.bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
            # str cast in case of _ProxyEmojis
            return emoji_lookup[str(emoji)]
        except asyncio.TimeoutError:
            return None
        finally:
            if autodelete:
                await msg.delete()
