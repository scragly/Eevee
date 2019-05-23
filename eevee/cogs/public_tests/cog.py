import asyncio
import time
import datetime
import json
import re
from io import BytesIO

import async_timeout
import discord
from PIL import Image, ImageDraw, ImageOps

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
            content = f'{len(embeds)} Embeds'
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

    @group(name='embed', invoke_without_command=True)
    async def _embed(self, ctx, title=None, content=None, colour=None,
                     icon_url=None, image=None, thumbnail=None, footer=None,
                     footer_icon=None, plain_msg=''):
        await ctx.embed(title=title, description=content, colour=colour,
                        icon=icon_url, image=image, thumbnail=thumbnail,
                        plain_msg=plain_msg, footer=footer,
                        footer_icon=footer_icon)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @_embed.command(name='error')
    async def _error(self, ctx, title, content=None, log_level='warning'):
        await ctx.error(title, content, log_level)

    @_embed.command(name='info')
    async def _info(self, ctx, title, content=None):
        await ctx.info(title, content)

    @_embed.command(name='warning')
    async def _warning(self, ctx, title, content=None):
        embed = utils.make_embed(title=title, content=content, msg_type='warning')
        await ctx.send(embed=embed)

    @_embed.command(name='success')
    async def _success(self, ctx, title, content=None):
        embed = utils.make_embed(title=title, content=content, msg_type='success')
        await ctx.send(embed=embed)

    @_embed.command(name='help')
    async def _help(self, ctx, title, content=None):
        embed = utils.make_embed(title=title, content=content, msg_type='help')
        await ctx.send(embed=embed)

    @command(aliases=['avatar'])
    async def avy(self, ctx, member: discord.Member = None, size: utils.bitround = 1024):
        member = member or ctx.author
        avy_url = member.avatar_url_as(size=size, static_format='png')
        try:
            colour = await utils.user_color(member)
        except OSError:
            colour = ctx.me.colour
        await ctx.embed(
            f"{member.display_name}'s Avatar", title_url=avy_url, image=avy_url, colour=colour)

    @command()
    async def cleanup(self, ctx, after_msg_id: int, channel_id: int = None):
        after_msg = await ctx.get.message(after_msg_id)
        channel = ctx.channel
        if channel_id:
            channel = ctx.get.channel(channel_id)

        def is_eevee(msg):
            return msg.author == ctx.bot.user

        try:
            deleted = await channel.purge(
                after=after_msg, check=is_eevee, bulk=True)
        except discord.Forbidden:
            deleted = await channel.purge(
                after=after_msg, check=is_eevee, bulk=False)

        del_count = len(deleted)

        embed = utils.make_embed(
            msg_type='success',
            title=f"Deleted {del_count} message{'s' if del_count > 1 else ''}"
        )

        result_msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await result_msg.delete()

    @command(aliases=['igpayatinlay'])
    async def piglatin(self, ctx, *words):
        if not words:
            return await ctx.send('Onay Ordsway Otay Onvertcay')
        result = []
        for word in words:
            if not word:
                result.append('')
                continue
            word = word.lower()
            pattern = re.compile('[a,e,i,o,u]')
            y = 'y'
            tail = 'a' + y
            if word.startswith(y):
                result.append(word + y + tail)
                continue
            first_vowel = pattern.search(word)
            if not first_vowel:
                result.append(word + tail)
                continue
            first_vowel = first_vowel.group()
            if word.find(first_vowel) == 0:
                result.append(word + y + tail)
                continue
            first, second = word.split(first_vowel, 1)
            result.append(first_vowel + second + first + tail)
        await ctx.send(' '.join(result))

    async def circle_crop(self, img_url):
        async with self.bot.session.get(img_url) as r:
            data = BytesIO(await r.read())
        img = Image.open(data)
        size = img.size
        with Image.new('L', size, 255) as mask:
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=0)
            del draw
            img = img.convert('RGBA')
            output = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
            output.paste(0, mask=mask)
            b = BytesIO()
            output.save(b, 'png')
            b.seek(0)
            return b

    @command()
    async def profile_preview(self, ctx, url=None):
        img_urls = []
        if not url:
            if ctx.message.attachments:
                for img in ctx.message.attachments:
                    img_urls.append(img.url)
            else:
                img_urls.append(ctx.author.avatar_url_as(format='png'))
        else:
            img_urls.append(url)
        imgs = []
        for img_url in img_urls:
            imgs.append(await self.circle_crop(img_url))

        for img in imgs:
            await ctx.send(file=discord.File(img, filename='circle.png'))

    @command()
    async def vote(self, ctx, title, *, content):
        uv = ctx.get.emoji('upvote')
        dv = ctx.get.emoji('downvote')
        msg = await ctx.embed(title, content)
        await msg.add_reaction(uv)
        await asyncio.sleep(0.5)
        await msg.add_reaction(dv)
        await ctx.message.delete()
