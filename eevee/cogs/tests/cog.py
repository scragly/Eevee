import re
import os
import asyncio
import json
import async_timeout
import pkgutil
import numpy
import random
import discord
from discord.ext import commands
from discord.ext.commands import Paginator

from eevee import command, group, checks, Cog
from eevee.utils import make_embed, get_match
from eevee.utils.converters import Guild
from eevee.utils.formatters import bold


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

    @group(name='embed', invoke_without_command=True)
    async def _embed(self, ctx, title=None, content=None, colour=None,
                     icon_url=None, image=None, thumbnail=None,
                     plain_msg=''):
        await ctx.embed(title=title, description=content, colour=colour,
                        icon=icon_url, image=image, thumbnail=thumbnail,
                        plain_msg=plain_msg)

    @_embed.command(name='error')
    async def _error(self, ctx, title, content=None, log_level='warning'):
        await ctx.error(title, content, log_level)

    @_embed.command(name='info')
    async def _info(self, ctx, title, content=None):
        await ctx.info(title, content)

    @_embed.command(name='warning')
    async def _warning(self, ctx, title, content=None):
        embed = make_embed(title=title, content=content, msg_type='warning')
        await ctx.send(embed=embed)

    @_embed.command(name='success')
    async def _success(self, ctx, title, content=None):
        embed = make_embed(title=title, content=content, msg_type='success')
        await ctx.send(embed=embed)

    @_embed.command(name='help')
    async def _help(self, ctx, title, content=None):
        embed = make_embed(title=title, content=content, msg_type='help')
        await ctx.send(embed=embed)

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

    @command()
    async def ask_test(self, ctx, *, options: str = None):
        cek = '\u20e3'
        # react_dict = {
        #     "1" : {
        #         "emoji":"1"+cek,
        #         "value":1
        #     },
        #     "2" : {
        #         "emoji":"2"+cek,
        #         "value":2
        #     },
        #     "3" : {
        #         "emoji":"3"+cek,
        #         "value":3
        #     }
        # }
        react_dict = None # comment out to test custom react_dict
        options = options.split(' ') if options else None
        response = await ctx.ask(
            'pls confirm', timeout=10, options=options)
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
    async def cleanup(self, ctx, after_msg_id: int):
        after_msg = await ctx.get.message(after_msg_id)
        def is_eevee(msg):
            return msg.author == ctx.bot.user
        try:
            deleted = await ctx.channel.purge(
                after=after_msg, check=is_eevee, bulk=True)
        except discord.Forbidden:
            deleted = await ctx.channel.purge(
                after=after_msg, check=is_eevee, bulk=False)
        embed = make_embed(
            msg_type='success',
            title='Deleted {} message{}'.format(
                len(deleted), "s" if len(deleted) > 1 else ""))
        result_msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await result_msg.delete()

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
    async def avy(self, ctx, member: discord.Member, size: int = 1024):
        await ctx.send(member.avatar_url_as(size=size))

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
    async def xkcd(self, ctx, comic_number: int = None):
        url_num = f"{comic_number}/" if comic_number else ""
        url = f"https://xkcd.com/{url_num}info.0.json"
        async with async_timeout.timeout(10):
            async with ctx.bot.session.get(url) as response:
                xkcd_data = await response.json()
        title = (f"{xkcd_data['safe_title']} - "
                 f"{xkcd_data['num']} - "
                 f"{xkcd_data['year']}/{xkcd_data['month']}/{xkcd_data['day']}")
        await ctx.embed(title, footer=xkcd_data['alt'], image=xkcd_data['img'])

    @command(aliases=["hello", "g'day", "gday", "whatsupcobba", "topofthemorning", "hola"])
    async def hi(self, ctx):
        await ctx.embed(f"Hi {ctx.author.display_name} \U0001f44b")

    @command()
    @checks.is_owner()
    async def sql(self, ctx, *, query):
        results = await ctx.bot.dbi.execute_transaction(query)
        if len(results) == 1:
            results = results[0]
        await ctx.codeblock(results, "")

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
                for _, ext, ispkg in pkgutil.iter_modules([path])
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
    async def raid_help(self, ctx):
        # f"`{'Level':<23}:` {pokemon.raid_level}\n"
        title = "Raid Coordination Help"
        icon = ("https://cdn.discordapp.com/avatars/346759953006198784/"
                "47cddf18228a9f9a664dfa9b2ea4155e.png?size=256")
        content = ['**Key**', ("<> denote required arguments\n"
                               "[] denote optional arguments")]
        raidmgmt = {
            '!raid <species>':"Hatches Egg channel",
            '!weather <weather>':"Sets in-game weather",
            '!timerset <minutes>':"Sets hatch/raid timer",
            '!starttime <time>':"Sets start time",
            '<google maps link>':"Updates raid location"
        }
        rsvp = {
            '!(i/c/h) [total] [team counts]':(
                "Marks you as interested/coming/here.\n"
                "    `[total]`\n        Total # of trainers in the group.\n"
                "    `[team counts]`\n        # of trainers in each team\n"
                "        Example: `3m` = 3 Mystic."),
            '!starting [team]':"Moves trainers from 'here' to 'lobby'"
        }
        raidmgmt_list = []
        for cmd, details in raidmgmt.items():
            raidmgmt_list.append(f"**`{cmd}`**\n    {details}")
        rsvp_list = []
        for cmd, details in rsvp.items():
            rsvp_list.append(f"**`{cmd}`**\n    {details}")
        fields = {
            "RAID MANAGEMENT":'\n'.join(raidmgmt_list),
            "RSVP":'\n'.join(rsvp_list)
        }
        await ctx.embed(
            title, '\n'.join(content), icon=icon, fields=fields, inline=True)

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
