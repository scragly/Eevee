import asyncio
import datetime
import os
import pkgutil
import random
import re

import discord
import numpy

from discord.ext import commands

from eevee import Cog, checks, command
from eevee.utils.converters import Guild, Multi

PBOT_APPID = 'un08c68977'
PBOT_UKEY = 'd6ec6b1babce597b27050962926f3a4c'


class Tests(Cog):
    """Test Features"""

    async def __local_check(self, ctx):
        if not self.tables:
            pass
        owner = await checks.check_is_co_owner(ctx)
        enabled = await checks.check_cog_enabled(ctx)
        return all((owner, enabled))

    @command()
    async def log_test(self, ctx, *, log_msg):
        self.logger.info(log_msg)
        await ctx.send(f'Sent the following log msg:\n{log_msg}')

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

    @command(category="Server Config")
    async def _test(self, ctx):
        await ctx.send(f"{self.__class__.__name__}Enabled")

    @command()
    async def ok(self, ctx):
        await ctx.ok()

    @command()
    async def aemoji(self, ctx):
        """Run a command as a different member."""
        await ctx.send("<a:ablobunamused:393721462634184705>")

    @command()
    async def getemoji(self, ctx):
        """Get an emoji from any connected server."""
        await ctx.send(str(ctx.guild.emojis))

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
    async def set_admin(self, ctx, role: discord.Role):
        await ctx.setting('AdminRole', role.id)
        await ctx.send(f'Set {role.name} as this guilds Admin Role.')

    @command()
    async def set_mod(self, ctx, role: discord.Role):
        await ctx.setting('ModRole', role.id)
        await ctx.send(f'Set {role.name} as this guilds Mod Role.')

    @command()
    async def find_guild(self, ctx, *, guild: Guild):
        if guild:
            await ctx.send(f"{guild.name} - {guild.id}")
        else:
            await ctx.send("Guild not found.")

    @command()
    async def get_member(self, ctx, *, member: discord.Member):
        await ctx.send(f"{member.name} - {member.id}")

    @command()
    async def delete_msg(self, ctx, *message_ids: int):
        for msg_id in message_ids:
            msg = await ctx.get.message(id=msg_id)
            if not msg:
                return
            await msg.delete()
        await asyncio.sleep(5)
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @command()
    async def codeblock(self, ctx, syntax, *, content):
        await ctx.codeblock(content, syntax=syntax)

    @commands.command()
    async def horserace(self, ctx, amount: int, horse: str):
        """Choose a horse to bet on!

        Aria - 40%
        Bally - 30%
        Bellagio - 15%
        Flamingo - 10%
        Luxor - 5%
        """
        max_bet = 100
        min_max_betters = (80, 100)
        horse_data = {
            'Aria': 0.4,
            'Bally': 0.3,
            'Bellagio': 0.15,
            'Flamingo': 0.1,
            'Luxor': 0.05,
        }
        if horse not in horse_data.keys():
            return await ctx.send("Please pick a valid horse.")
        bets = {}
        for rhorse in numpy.random.choice(
                list(horse_data.keys()),
                numpy.random.randint(min_max_betters[0], min_max_betters[1]),
                p=list(horse_data.values())):
            bets[rhorse] = bets.setdefault(rhorse, list())
            bets[rhorse].append(numpy.random.choice(max_bet))
        betters = sum([len(vals) for vals in bets.values()]) + 1
        bet_total = sum([sum(vals) for vals in bets.values()]) + amount
        first, second, third = numpy.random.choice(
            list(horse_data.keys()), 3, replace=False, p=list(horse_data.values()))
        winner_bet = bets.get(first, [0,])
        win_count = len(winner_bet) + (1 if horse == first else 0)
        win_total = sum(winner_bet) + amount
        payout_pd = round((bet_total / win_total) * 0.9, 2)
        payout = round((bet_total * amount / win_total) * 0.9, 2) if horse == first else 0
        result = "Winner!" if horse == first else "Better Luck Next Time"
        fields = {
            "Results":(f"**First:** {first}\n"
                       f"**Second:** {second}\n"
                       f"**Third:** {third}"),
            "Stats"  :(f"**Betters:** {betters}\n"
                       f"**Winners:** {win_count}\n"
                       f"**Bet Pool:** ${bet_total}\n"
                       f"**Payout:** ${payout_pd} per $1")
        }
        await ctx.embed(f"{result}", f"You've won ${payout}", fields=fields)

    @command()
    async def tree(self, ctx):
        tree_dict = {}
        def get_modules(path):
            return {
                ext : get_modules(os.path.join(path, ext)) if ispkg else False
                for __, ext, ispkg in pkgutil.iter_modules([path])
            }
        tree_dict['eevee'] = get_modules(ctx.bot.eevee_dir)
        tree_lines = []
        def build_tree(data, level, last=False):
            if level == 0:
                padding = ""
            elif last and level > 2:
                padding = " │   "+("     "*(level-2))
            elif last and level > 1:
                padding = "     "*(level-1)
            else:
                padding = " │   "*(level-1)
            count = 0
            total = len(data)
            for k, v in data.items():
                count += 1
                prefix = " ├── "
                if level == 0:
                    prefix = ""
                elif count == total:
                    prefix = " └── "
                buffer = padding+prefix
                if v:
                    tree_lines.append(f"{buffer}[{k}]")
                    build_tree(v, level+1, total == count)
                else:
                    tree_lines.append(f"{buffer}{k}.py")
        build_tree(tree_dict, 0)
        await ctx.codeblock('\n'.join(tree_lines), 'css')

    @command()
    async def sql_test(self, ctx, from_msg_id: int, process: bool = False):
        table = ctx.bot.dbi.tablenew('command_log')
        msg_id = table['message_id']
        auth_id = table['author_id']
        table.query(msg_id.sum).order_by(msg_id, asc=False).group_by(msg_id)
        table.query.where(msg_id > from_msg_id)
        table.query.where(
            (auth_id == 174764205927432192,
             auth_id == 394529085923262464))
        if process:
            data = await table.query.get()
            return await ctx.codeblock(data)
        sql = f"{table.query.sql[0]}\n\n-- VALUES --\n{table.query.sql[1]}"
        await ctx.codeblock(sql, "sql")

    @command()
    async def roll(self, ctx, *dice):
        def die_roll(sides: int):
            return random.choice(range(1, sides+1))
        def process_dice(d):
            rolls, sides = map(int, d.split('d'))
            return [die_roll(sides) for i in range(rolls)]
        results = []
        for d in dice:
            results.append(process_dice(d))
        msg = '\n'.join(', '.join(map(str, l)) for l in results)
        return await ctx.embed("Results", msg)

    @command()
    async def test_default(self, ctx, guild: discord.Guild = None):
        guild = guild or ctx.guild
        names = ["general", "lounge", "chat"]
        def can_use(channel):
            if not channel.name in names:
                return False
            perms = channel.permissions_for(guild.me)
            return perms.send_messages and perms.read_messages
        results = list(filter(can_use, guild.text_channels))
        await ctx.send(str(results))

    @command()
    async def show_deleted(self, ctx, count: int = 1,
                           channel: discord.TextChannel = None):
        msg_table = ctx.bot.dbi.table('discord_messages')
        msg_table.query(
            'message_id', 'sent', 'is_edit', 'author_id', 'clean_content',
            'embeds', 'attachments')
        msg_table.query.where(channel_id=channel or ctx.channel.id)
        msg_table.query.where(deleted=True)
        msg_table.query.order_by('message_id', 'sent', asc=False)
        msg_table.query.limit(count)
        print(msg_table.query.sql())
        messages = await msg_table.query.get()

        if not messages:
            return await ctx.embed(
                "I didn't find any deleted messages, sorry!")

        msg_data = {}
        for msg in messages:
            author = await ctx.get.user(msg['author_id'])
            date = datetime.datetime.fromtimestamp(int(msg['sent']))
            date_str = date.strftime('%Y-%m-%d %H:%M:%S')
            content = msg['clean_content']
            embeds = msg['embeds']
            attachments = msg['attachments']
            if len(embeds) > 1:
                embed_content = f'{len(embeds)} Embeds'
            elif embeds:
                embed = embeds[0]
                embed_content = []
                if embed.get('author'):
                    embed_content.append(
                        f"AuthorTitle: {embed['author']['name']}")
                if embed.get('title'):
                    embed_content.append(
                        f"Title: {embed['title']}")
                if embed.get('description'):
                    embed_content.append(
                        f"Description: {embed['description']}")
                if embed.get('fields'):
                    embed_content.append(
                        f"Field Count: {len(embed['fields'])}")
                if embed.get('color'):
                    embed_content.append(
                        f"Colour: {embed['color']}")
                if embed_content:
                    embed_content = '\n'.join(embed_content)
                else:
                    embed_content = '1 Embed'

                content += f"\n**Embeds:**\n{embed_content}"

            if attachments:
                att_content = '\n'.join(attachments)
                content += f"\n**Attachments:**\n{att_content}"

            if not content:
                content = "No content"

            msg_data[f"{author.display_name} | {date_str}"] = content

        if count > 1:
            title = 'Recently Deleted Messages'
        else:
            title = 'Last Deleted Message'

        await ctx.embed(title, fields=msg_data)

    @command()
    async def clonechannel(self, ctx, channel_id: int):
        channel = ctx.get.channel(channel_id)
        if not channel:
            return await ctx.error('No Channel Found')
        ch_types = {
            discord.TextChannel : discord.ChannelType.text,
            discord.VoiceChannel : discord.ChannelType.voice,
            discord.CategoryChannel : discord.ChannelType.category
        }
        channel_type = ch_types[type(channel)]
        await ctx.guild._create_channel(
            channel.name, dict(channel.overwrites), channel_type,
            channel.category, "Clone Test")

    @command()
    async def uniontest(self, ctx, test: Multi(discord.Member, discord.TextChannel, int),  *, test_content=None):
        await ctx.send(str(type(test)))

    @command()
    async def ask_test(self, ctx, *, options: str = None):
        options = options.split(' ') if options else None
        response = await ctx.ask(
            'pls confirm', timeout=10, options=options)
        await ctx.send(str(response))

    @command()
    async def movechan(self, ctx, position: int, channel: discord.TextChannel):
        await channel.edit(position=position)
        await ctx.ok()

    @command()
    async def sortchan(self, ctx, reverse: bool = False):
        """Sort the current categories channels by alphabetical order."""
        channels = enumerate(sorted(
            ctx.channel.category.channels,
            key=lambda item: item.name,
            reverse=reverse))

        for position, channel in channels:
            await channel.edit(position=position)

        await ctx.ok()
