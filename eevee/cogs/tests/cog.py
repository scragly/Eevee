import re
import asyncio
import datetime
import logging

from collections import Counter

import discord
from discord.ext import commands
from discord.ext.commands import EmojiConverter, BadArgument

from eevee import command, checks, utils
from eevee.utils import make_embed

from eevee.core.data_manager import schema

from eevee.core.data_manager.dbi import DatabaseInterface

class CogTable:

    table_config = {
        "name" : "base_default_table",
        "columns" : {
            "id" : {"cls" : schema.IDColumn},
            "value" : {"cls" : schema.StringColumn}
        },
        "primaries" : ("id")
    }

    def __init__(self, bot):
        self.dbi: DatabaseInterface = bot.dbi
        self.bot = bot

    def convert_columns(self, columns_dict=None):
        columns = []
        for k, v in columns_dict.items():
            col_cls = v.pop('cls', schema.Column)
            columns.append(col_cls(k, **v))
        return columns

    async def setup(self, table_name=None, columns: list = None, *, primaries=None):
        table_name = table_name or self.table_config["name"]
        table = self.dbi.table(table_name)
        exists = table.exists()
        if not exists:
            columns = self.convert_columns(self.table_config["columns"])
            primaries = primaries or self.table_config["primaries"]
            table = await table.create(
                self.dbi, table_name, columns, primaries=primaries)
        return table


class TestsCogTable(CogTable):
    table_config = {
        "name" : "tests_cog_table",
        "columns" : {
            "id" : {"cls" : schema.IDColumn},
            "value" : {"cls" : schema.StringColumn}
        },
        "primaries" : ("id")
    }

class Tests:
    """Test Features"""

    def __init__(self, bot):
        self.bot = bot
        self._cog_table = None
        self.log = logging.getLogger('eevee.cogs.tests.Tests')
        self.log.warning('self.log')
        bot.logger.warning('bot.logger')

    async def __local_check(self, ctx):
        if not self._cog_table:
            self._cog_table = await TestsCogTable(self.bot).setup()
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

    @command()
    async def cleanup(self, ctx, count=10):
        def is_eevee(msg):
            return msg.author == ctx.bot.user
        deleted = await ctx.channel.purge(limit=count, check=is_eevee, bulk=False)
        embed = make_embed(
            msg_type='success',
            title='Deleted {} message{}'.format(
                len(deleted), "s" if len(deleted) > 1 else ""))
        result_msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await result_msg.delete()

    @command()
    async def rpoll(self, ctx, question, *answers):
        # split the answers
        raw_emoji_list = answers[::2]
        answer_list = answers[1::2]

        # get emoji objects if valid custom emoji
        emoji_list = []
        for emoji in raw_emoji_list:
            try:
                emoji = await EmojiConverter().convert(ctx, emoji)
            except BadArgument:
                # don't want the whole command to stop here
                pass

            # maybe check if someone elses custom-emoji and use your
            # emoji-stealing function here

            emoji_list.append(emoji)

        # make the message string asking people the question
        ask_msg = '\n'.join([f"{e} - {a}" for e, a in zip(emoji_list, answer_list)])

        # make your embed to ask people their shitty opinions
        embed = discord.Embed(
            color=discord.Color.default(),
            title=f"Poll: {question}",
            description=f"{ask_msg}",
            timestamp=datetime.datetime.utcnow())
        embed.set_footer(text="Vote using the reactions below.")

        # send the poll embed
        poll = await ctx.send(embed=embed)

        # build the check to collate the votes
        votes = {}
        def check(reaction, user):
            if user.id == ctx.bot.user.id:
                return False
            if reaction.emoji in emoji_list:
                votes[user.id] = reaction.emoji
                return False

        # slowly add reactions as quick as the API lets us
        for e in emoji_list:
            await poll.add_reaction(e)

        # wait for reactions
        try:
            await ctx.bot.wait_for('reaction_add', timeout=10, check=check)
        except asyncio.TimeoutError:
            pass

        # build results msg
        emoji_votes = Counter(votes.values())
        results = [f"{e} - {c}" for e, c in emoji_votes.most_common()]
        if not results:
            results_msg = "**No Votes - No Winner**"
        else:
            result = '\n'.join(results)
            results_msg = f"**Results**\n{result}\n\n"

        # get old message's embed for editing
        embed = poll.embeds[0]
        embed.description = f"{embed.description}\n\n{results_msg}"

        # clean reactions away
        try:
            await poll.clear_reactions()
        except discord.Forbidden:
            # didn't have manage_messages so give up
            pass

        # submit edit
        await poll.edit(embed=embed)

    @command()
    async def set_admin(self, ctx, role: discord.Role):
        await ctx.setting('AdminRole', role.id)
        await ctx.send(f'Set {role.name} as this guilds Admin Role.')

    @command()
    async def set_mod(self, ctx, role: discord.Role):
        await ctx.setting('ModRole', role.id)
        await ctx.send(f'Set {role.name} as this guilds Mod Role.')

    @command()
    async def table_test(self, ctx):
        cog_tables = CogTables(ctx.bot)
        await cog_tables.setup()
        await ctx.send('done')
