import re

import discord
from discord.ext import commands

from eevee import command, checks, utils

class Tests:
    """Test Features"""

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        owner = await checks.check_is_co_owner(ctx)
        enabled = await checks.check_cog_enabled(ctx)
        return all((owner, enabled))

    @command()
    async def thumbtest(self, ctx, *, url=None):
        """Test a thumbnail image in an embed."""
        attachments = ctx.message.attachments
        if attachments:
            url = attachments[0].url

        embed = discord.Embed()
        embed.set_thumbnail(url=url)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send(
                "You've provided an incorrect URL, or I need the ",
                "`Embed links` permission to send this")

    @command()
    async def embed_test(self,
                         ctx,
                         title=None,
                         content=None,
                         msg_type='',
                         colour=None,
                         icon_url=None,
                         image=None,
                         thumbnail=None):
        embed = utils.make_embed(
            msg_type=msg_type, title=title, content=content, msg_colour=colour,
            guild=ctx.guild, icon=icon_url, image=image, thumbnail=thumbnail)
        await ctx.send(embed=embed)

    @command(category="Server Config")
    async def _test(self, ctx):
        await ctx.send(f"{self.__class__.__name__}Enabled")

    @command()
    async def aemoji(self, ctx):
        """Run a command as a different member."""
        await ctx.send("<a:ablobunamused:393721462634184705>")

    @command()
    async def getemoji(self, ctx):
        """Run a command as a different member."""
        await ctx.send(str(ctx.guild.emojis))

    @command()
    async def ask_test(self, ctx, *, options: str = None):
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
            }
        }
        react_dict = None # comment out to test custom react_dict
        options = options.split(' ') if options else None
        response = await ctx.ask(
            'pls confirm', timeout=10, options=options, react_dict=react_dict)
        await ctx.send(str(response))

    def process_template(self, message, author, guild):
        def template_replace(match):
            if match.group(3):
                if match.group(3) == 'user':
                    return author.mention
                elif match.group(3) == 'server':
                    return guild.name
                else:
                    return match.group(0)
            match_type = match.group(1)
            full_match = match.group(0)
            match = match.group(2)
            if match_type == "@":
                member = guild.get_member_named(match)
                if match.isdigit() and not member:
                    member = guild.get_member(int(match))
                return member.mention if member else full_match
            elif match_type == "#":
                channel = discord.utils.get(guild.channels, name=match)
                if match.isdigit() and not channel:
                    channel = guild.get_channel(int(match))
                return channel.mention if channel else full_match
            elif match_type == '&':
                role = discord.utils.get(guild.roles, name=match)
                if match.isdigit() and not role:
                    role = discord.utils.get(guild.roles, id=match)
                return role.mention if role else full_match
        template_pattern = r'{(@|#|&)([^{}]+)}|{(user|server)}'
        return re.sub(template_pattern, template_replace, message)

    @command()
    async def template_test(self, ctx, *, msg_str):
        await ctx.send(self.process_template(msg_str, ctx.author, ctx.guild))

    @command()
    async def test(self, ctx):
        await ctx.send('test')
