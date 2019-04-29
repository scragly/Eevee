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
        self.timezones = None
        self.get_timezones()

    def get_timezones(self):
        zone_tab = pytz.open_resource('zone.tab')
        try:
            data = {}
            for line in zone_tab:
                line = line.decode('UTF-8')
                if line.startswith('#'):
                    continue
                code, coordinates, zone = line.split(None, 4)[:3]
                if zone not in pytz.all_timezones_set:
                    continue
                try:
                    data[code].append(zone)
                except KeyError:
                    data[code] = [zone]
            self.timezones = data
        finally:
            zone_tab.close()

    def timezone_names(self):
        tznames = {}
        for tz in pytz.all_timezones:
            name = pytz.timezone(tz).localize(datetime.datetime.now()).tzname()
            try:
                tznames[name].append(tz)
            except KeyError:
                tznames[name] = [tz,]
        return tznames

    def match_timezone(self, query):
        # try it as-is first
        try:
            pytz.timezone(query)
            return [(query, 100),]
        except pytz.UnknownTimeZoneError:
            pass

        # check if in tz names
        tz_names = self.timezone_names()
        if query.upper() in tz_names:
            return [(tz, 100) for tz in tz_names[query.upper()]]

        # fuzzymatch against all timezones as last resort
        matches = fuzzymatch.get_matches(tz_names.keys(), query, 80)

        commontz_matches = fuzzymatch.get_matches(
            pytz.common_timezones, query, 90, True)

        if commontz_matches:
            matches.extend(commontz_matches)

        fullmatches = [(tz, 100) for tz, s in matches if s == 100]
        if len(fullmatches) == 1:
            return fullmatches

        return matches

    async def get_timezone(self, member_id):
        table = self.bot.dbi.table('member_timezones')
        table.query('timezone')
        table.query.where(member_id=member_id)
        return await table.query.get_value()

    async def verify_timezone(self, ctx, timezone):

        # detect utc offset values
        try:
            tzoffset = datetime.timedelta(hours=float(timezone))
            datetime.timezone(tzoffset)
        except ValueError:
            pass
        else:
            return timezone

        # try matching if not an offset
        results = self.match_timezone(timezone)

        if not results:
            return None

        if len(results) == 1:
            return results[0][0]

        result_str = [f"{tz} ({s}%)" for tz, s in results]
        results = [tz for tz, s in results]

        which_msg = await ctx.embed(
            "Which of these matches?",
            '\n'.join(result_str),
            msg_type='help',
            footer="To stop, reply with 'cancel'.")

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        reply_msg = await ctx.bot.wait_for('message', check=check)

        await which_msg.delete()

        if reply_msg.content.lower() == 'cancel':
            return None

        return fuzzymatch.get_match(results, reply_msg.content, 95, True)[0]

    @command()
    async def tztest(self, ctx, *, timezone):

        match = await self.verify_timezone(ctx, timezone)

        if not match:
            return await ctx.error('No Match')

        tz_time = pendulum.now(match).format('HH:mm, dddd')

        await ctx.success(f'Match: {match} | {tz_time}')

    @group(invoke_without_command=True, aliases=['timezone'])
    async def tz(self, ctx, member: discord.Member = None):
        """Shows a member's timezone"""
        member = member or ctx.author
        timezone = await self.get_timezone(member.id)
        if not timezone:
            return await ctx.error(
                f'{member.display_name} has not set a timezone yet.',
                f'To set one, use the `{ctx.prefix}tz set` command like so:\n'
                f'```{ctx.prefix}tz set US/Eastern```\n'
                f"[List of all available timezones]({self.tzdburl})")
        return await ctx.embed(f"{member.display_name}'s Timezone", timezone)

    @tz.command(name='list')
    async def tz_list(self, ctx):
        await ctx.embed("Available Timezones List", title_url=self.tzdburl)

    @tz.command(name='set')
    async def _set(self, ctx, timezone=None, member: discord.Member = None):
        """Sets a member's timezone. Only co-owners can set other's tzs."""

        if member and not await checks.check_is_co_owner(ctx):
            return await ctx.error('You can only set your own timezone.')

        member = member or ctx.author

        if timezone:
            timezone = await self.verify_timezone(ctx, timezone)
            if not timezone:
                return await ctx.error('Invalid Timezone.')

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
        timezone = await self.verify_timezone(ctx, timezone)
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
