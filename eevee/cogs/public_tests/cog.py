import time
import datetime
import json
import pendulum

import discord

from eevee import group, command, checks, utils

class BaseConverter(object):
    decimal_digits = "0123456789"

    def __init__(self, digits):
        self.digits = digits

    def from_decimal(self, i):
        return self.convert(i, self.decimal_digits, self.digits)

    def to_decimal(self, s):
        return int(self.convert(s, self.digits, self.decimal_digits))

    def convert(number, fromdigits, todigits):
        # Based on http://code.activestate.com/recipes/111286/
        if str(number)[0] == '-':
            number = str(number)[1:]
            neg = 1
        else:
            neg = 0

        # make an integer out of the number
        x = 0
        for digit in str(number):
            x = x * len(fromdigits) + fromdigits.index(digit)

        # create the result in base 'len(todigits)'
        if x == 0:
            res = todigits[0]
        else:
            res = ""
            while x > 0:
                digit = x % len(todigits)
                res = todigits[digit] + res
                x = int(x / len(todigits))
            if neg:
                res = '-' + res
        return res
    convert = staticmethod(convert)

class PublicTests:
    """Test commands that are open for public usage."""
    def __init__(self, bot):
        self.bot = bot

    async def get_prefixes(self, guild_id, bot_id=None):
        table = self.bot.dbi.tablenew('bot_prefixes')
        if bot_id:
            table.query('prefixes')
            table.query.where(guild_id=guild_id, bot_id=bot_id)
            try:
                return await table.query.get_value()
            except IndexError:
                return None
        else:
            table.query('prefixes', 'bot_id')
            table.query.where(guild_id=guild_id)
            try:
                return await table.query.get()
            except IndexError:
                return None

    async def set_prefixes(self, guild_id, bot_id, prefixes: list):
        await self.bot.dbi.upsert(
            'bot_prefixes', primary=['bot_id', 'guild_id'], bot_id=bot_id,
            guild_id=guild_id, prefixes=prefixes)
        return prefixes

    async def add_prefixes(self, bot_id, guild_id, prefixes: list):
        existing = await self.get_prefixes(bot_id, guild_id)
        prefixes.extend(existing)
        await self.set_prefixes(bot_id, guild_id, prefixes)
        return prefixes

    async def rm_prefixes(self, bot_id, guild_id, prefixes: list):
        existing = await self.get_prefixes(bot_id, guild_id)
        prefixes.extend(existing)
        await self.set_prefixes(bot_id, guild_id, prefixes)
        return prefixes

    async def del_bot(self, guild_id, bot_id):
        await self.bot.dbi.delete('bot_prefixes',
                                  bot_id=bot_id,
                                  guild_id=guild_id)

    @group(invoke_without_command=True)
    async def botprefixes(self, ctx, *, bot: discord.Member = None):
        if not bot:
            prefixes = []
            results = await self.get_prefixes(ctx.guild.id)
            for botdata in results:
                bot = ctx.get.member(botdata['bot_id'])
                prefixlist = [f'`"{p}"`' for p in botdata['prefixes']]
                prefixes.append(f"{bot.mention}\n{', '.join(prefixlist)}")
            await ctx.embed('Bot Prefixes', '\n'.join(prefixes))
        else:
            if not bot.bot:
                return await ctx.error("That's not a bot.")
            prefixes = await self.get_prefixes(ctx.guild.id, bot.id)
            await ctx.send(str(prefixes))

    @botprefixes.command(name='set')
    async def _set(self, ctx, bot: discord.Member, *prefixes):
        if not bot.bot:
            return await ctx.error("That's not a bot.")
        await self.set_prefixes(ctx.guild.id, bot.id, list(prefixes))
        return await ctx.success(
            f"Registered prefixes {', '.join(prefixes)} for {bot.display_name}")

    @botprefixes.command(name='add')
    async def _add(self, ctx, bot: discord.Member, *prefixes):
        if not bot.bot:
            return await ctx.error("That's not a bot.")
        all_prefixes = await self.add_prefixes(ctx.guild.id, bot.id, list(prefixes))
        return await ctx.success(
            f"Registered new prefixes {', '.join(prefixes)} for {bot.display_name}",
            f"Full list:\n{', '.join(all_prefixes)}")

    @botprefixes.command(name='rm', aliases=['remove', 'delete', 'clear'])
    async def _rm(self, ctx, *, bot: discord.Member):
        await self.del_bot(ctx.guild.id, bot.id)
        return await ctx.success(f"Removed bot {bot} from register.")

    @command()
    async def fuzz_test(self, ctx, word, *word_list):
        match, score = utils.get_match(word_list, word)
        if not match:
            return await ctx.send("The word did not meet the minimum likeness threshold.")
        await ctx.send(f"The word {word} matched {match} with a score of {score}")

    @group(invoke_without_command=True)
    async def mystxd(self, ctx):
        """How many times has Myst XD"""
        table = ctx.bot.dbi.table('discord_messages')
        table.query(table['*'].count).where(author_id=402159684724719617)
        table.query.where(table['clean_content'].ilike('%xd%'))
        xds = await table.query.get_value()
        await ctx.embed(f"I've seen Myst XD {xds} times.")

    @mystxd.command(aliases=['hr'])
    async def past(self, ctx, minutes: int):
        """How many times has Myst XD in the past x mins"""
        after = time.time() - (minutes * 60)
        table = ctx.bot.dbi.table('discord_messages')
        table.query(table['*'].count).where(author_id=402159684724719617)
        table.query.where(table['clean_content'].ilike('%xd%'))
        table.query.where(table['sent'] > int(after))
        xds = await table.query.get_value()
        await ctx.embed(f"I've seen Myst XD {xds} times in {minutes} mins.")

    @command()
    async def show_original(self, ctx, message_id: int):
        msg_table = ctx.bot.dbi.table('discord_messages')
        msg_table.query(
            'message_id', 'sent', 'is_edit', 'author_id', 'clean_content',
            'embeds', 'attachments')
        msg_table.query.where(message_id=message_id)
        msg_table.query.where(is_edit=False)
        msg_table.query.order_by('message_id', 'sent', asc=False)
        msg_table.query.limit(1)

        msg = await msg_table.query.get_first()

        print(msg)

        if not msg:
            return await ctx.embed(
                "I didn't find any deleted messages, sorry!")

        author = await ctx.get.user(msg['author_id'])
        date = datetime.datetime.fromtimestamp(int(msg['sent']))
        date_str = date.strftime('%Y-%m-%d %H:%M:%S')
        content = msg['clean_content']
        embeds = msg['embeds']
        if len(embeds) > 1:
            embed_content = f'{len(embeds)} Embeds'
        elif embeds:
            embed = json.loads(embeds[0])
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

        await ctx.embed(f"{author} | ID {message_id}", content)

    @command()
    async def base_converter(self, ctx, digits, *values):
        """Converts any number base with any representation of digits given."""
        base_convert = BaseConverter(digits)
        converted_values = map(base_convert.to_decimal, values)
        converted_values = map(str, converted_values)
        await ctx.send('\n'.join(converted_values))

    @command()
    async def quote(self, ctx, message_id: int):
        if message_id < 20000000000000000:
            return await ctx.error(
                "That doesn't seem to be a valid message ID!")
        table = ctx.bot.dbi.table('discord_messages')
        table.query(
            'clean_content', 'author_id', 'sent', 'channel_id', 'guild_id')
        table.query.where(message_id=message_id)
        table.query.order_by('sent', asc=False)
        message_data = await table.query.get_first()
        if not message_data:
            return await ctx.error(
                "I can't see a message with that ID, sorry!")
        sent_by = await ctx.get.user(message_data['author_id'])
        sent = datetime.datetime.fromtimestamp(message_data['sent'])
        sent_str = sent.strftime('%Y-%m-%d %H:%M:%S')
        channel = ctx.bot.get_channel(message_data['channel_id'])
        guild = ctx.get.guild(message_data['guild_id'])
        await ctx.embed(
            f'Quote from {sent_by}',
            utils.formatters.code(message_data['clean_content']),
            footer=f"Sent at {sent_str} in {channel} - {guild}")

    @command(aliases=['priv', 'privs'])
    async def privilege(self, ctx, member: discord.Member = None):
        if member:
            if not await checks.check_is_mod(ctx):
                return await ctx.error(
                    "Only mods can check other member's privilege level.")
        member = member or ctx.author
        ctx.author = member
        if not await checks.check_is_mod(ctx):
            return await ctx.info('Normal User')
        if not await checks.check_is_admin(ctx):
            return await ctx.info('Mod')
        if not await checks.check_is_guildowner(ctx):
            return await ctx.info('Admin')
        if not await checks.check_is_co_owner(ctx):
            return await ctx.info('Guild Owner')
        if not await checks.check_is_owner(ctx):
            return await ctx.info('Bot Co-Owner')
        return await ctx.info('Bot Owner')

    @command(aliases=["hello", "g'day", "gday", "whatsupcobba", "topofthemorning", "hola"])
    async def hi(self, ctx):
        await ctx.embed(f"Hi {ctx.author.display_name} \U0001f44b")
