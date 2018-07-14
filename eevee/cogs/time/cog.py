import datetime
import pytz

import pytzdata
import pendulum
import discord

from eevee import command, group, Cog, checks
from eevee.utils import fuzzymatch

class Time(Cog):
    """Time Tools"""
    def __init__(self, bot):
        self.bot = bot
        self.tzdburl = 'https://github.com/sdispater/pytzdata/blob/master/pytzdata/_timezones.py'

    def match_timezone(self, query):
        return fuzzymatch.get_match(pytzdata.timezones, query, 60)[0]

    async def get_timezone(self, member_id):
        table = self.bot.dbi.table('member_timezones')
        table.query('timezone')
        table.query.where(member_id=member_id)
        return await table.query.get_value()

    @command()
    async def tztest(self, ctx, *, timezone):
        results = fuzzymatch.get_matches(pytz.all_timezones, timezone)
        pytz.country_timezones
        if not results:
            await ctx.error('No Result')
        else:
            results = [f"{s}% - {tz}" for tz, s in results]
            await ctx.success('Matching with:', '\n'.join(results))

    @group(invoke_without_command=True, aliases=['timezone'])
    async def tz(self, ctx, member: discord.Member = None):
        """Shows a member's timezone"""
        member = member or ctx.author
        timezone = await self.get_timezone(member.id)
        if not timezone:
            if ctx.author == member:
                return await ctx.error(
                    f'{member.display_name} has not set a timezone yet.',
                    f'To set one, use the `{ctx.prefix}tz set` command like so:\n'
                    f'```{ctx.prefix}tz set US/Eastern```\n'
                    f"[List of all available timezones]({self.tzdburl})")
            return await ctx.error(f'{member.display_name} has not set a timezone yet.')
        return await ctx.embed(f"{member.display_name}'s Timezone", timezone)

    @tz.command(name='set')
    async def _set(self, ctx, timezone=None, member: discord.Member = None):
        """Sets a member's timezone"""
        member = member or ctx.author
        try:
            timezone = float(timezone)
        except ValueError:
            pass
        if isinstance(timezone, float):
            tzoffset = datetime.timedelta(hours=timezone)
            try:
                datetime.timezone(tzoffset)
            except ValueError as e:
                return await ctx.error(str(e).title())
        else:
            timezone = self.match_timezone(timezone)
            if not timezone:
                return await ctx.error(
                    'Invalid Timezone Provided.',
                    f"[List of all available timezones]({self.tzdburl})")

        table = ctx.bot.dbi.table('member_timezones')
        table.insert(
            member_id=member.id,
            timezone=str(timezone))
        table.insert.primaries('member_id')
        await table.insert.commit(do_update=True)

        await ctx.success(
            f'Timezone for {member.display_name} saved as {timezone}.')

    @tz.command(name='rm', aliases=['remove', 'del', 'delete', 'clear'])
    async def _rm(self, ctx, member: discord.Member = None):
        """Sets a member's timezone"""
        if member and not await checks.check_is_co_owner(ctx):
            return await ctx.error('You can only remove your own timezone.')
        member = member or ctx.author

        query = ctx.bot.dbi.table('member_timezones').query
        await query.delete(member_id=member.id)

        await ctx.success(
            f'Timezone for {member.display_name} removed.')

    @group(invoke_without_command=True)
    async def time(self, ctx, member: discord.Member = None):
        """Shows a member's current local time."""
        member = member or ctx.author
        timezone = await self.get_timezone(member.id)
        if not timezone:
            if ctx.author == member:
                return await ctx.error(
                    f'{member.display_name} has not set a timezone yet.',
                    f'To set one, use the `{ctx.prefix}tz set` command like so:\n'
                    f'```{ctx.prefix}tz set US/Eastern```\n'
                    f"[List of all available timezones]({self.tzdburl})")
            return await ctx.error(f'{member.display_name} has not set a timezone yet.')
        try:
            timezone = float(timezone)
        except ValueError:
            pass
        if isinstance(timezone, float):
            tzoffset = datetime.timedelta(hours=timezone)
            tz = datetime.datetime.utcnow() + tzoffset
            tz = tz.strftime('%H:%M, %A')
        else:
            tz = pendulum.now(timezone).format('HH:mm, dddd')
        await ctx.embed(f'Time for {member.display_name}', tz, footer=timezone)

    @time.command(name='tz', aliases=['timezones', 'timezone'])
    async def time_tz(self, ctx, timezone=None):
        timezone = timezone or 'UTC'
        timezone = self.match_timezone(timezone)
        try:
            timezone = float(timezone)
        except ValueError:
            pass
        if isinstance(timezone, float):
            tzoffset = datetime.timedelta(hours=timezone)
            tz = datetime.datetime.utcnow() + tzoffset
            tz = tz.strftime('%H:%M, %A')
        else:
            tz = pendulum.now(timezone).format('HH:mm, dddd')
        await ctx.embed(f'Time for {timezone}', tz)
