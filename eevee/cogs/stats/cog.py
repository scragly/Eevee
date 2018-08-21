import io
import typing

import discord
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from eevee import checks, command
from eevee.utils.converters import Guild


class Statistics:
    """Statistics Tools"""
    def __init__(self, bot):
        self.bot = bot

    @command()
    async def msgcount(self, ctx, member: typing.Union[discord.Member, Guild] = None):
        guild = None
        if isinstance(member, discord.Guild):
            if await checks.check_is_owner(ctx):
                guild = member
                member = ctx.author
            else:
                member = None

        guild = guild or ctx.guild
        member = member or ctx.author
        query = ctx.bot.dbi.table('discord_messages').query('sent')
        query.where(guild_id=guild.id, is_edit=False, author_id=member.id)
        query.order_by('sent', asc=False)
        data = await query.get_values()

        if not data:
            return await ctx.error(
                f"I haven't seen {member.display_name} before.")

        dates = mdates.epoch2num(data)

        fig, ax = plt.subplots(linewidth=0, sharey=True, tight_layout=True)
        fig.set_size_inches(8, 4)
        ax.tick_params(labelsize=12, color='lightgrey', labelcolor='lightgrey')

        locator = mdates.AutoDateLocator()
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))

        counts, bins, patches = ax.hist(dates, 10, facecolor='red', alpha=0.75)
        ax.set_xticks(bins)

        plot_bytes = io.BytesIO()
        fig.savefig(
            plot_bytes,
            format='png',
            facecolor='#32363C',
            transparent=True)
        plot_bytes.seek(0)
        fig.clf()

        fname = f"msgcount-{member.id}.png"
        plot_file = discord.File(plot_bytes, filename=fname)

        embed = await ctx.embed(
            f"Message Stats - {member.display_name} in {guild.name}", send=False)
        embed.set_image(url=f"attachment://{fname}")
        await ctx.send(file=plot_file, embed=embed)

    @command()
    async def mostactive(self, ctx):
        table = ctx.bot.dbi.table('discord_messages')
        query = table.query(
            'author_id',
            table['message_id'].count,
            "rank() over (order by count(message_id) desc) as rank")
        query.where(guild_id=ctx.guild.id, is_edit=False)
        query.order_by('count', asc=False)
        query.group_by('author_id')
        data = await query.get()

        if not data:
            return await ctx.error('No data found.')

        author_data = [m for m in data if m['author_id'] == ctx.author.id][0]

        data = {
            (
                str(ctx.get.member(m['author_id'], ctx.guild.id))
                if ctx.get.member(m['author_id'], ctx.guild.id) else str(m['author_id'])
            ) :m['count'] for m in data[:10]
        }

        if author_data and str(ctx.author) not in data:
            data["..."] = 0
            author_key = f"#{author_data['rank']} - {ctx.author}"
            data[author_key] = author_data['count']

        # ax.bar(x, y, color='r', width=1.0, linewidth=0, tick_label=labels)

        matplotlib.rc('font', family='Roboto Medium')

        fig, ax = plt.subplots(linewidth=0, sharey=True, tight_layout=True)
        fig.set_size_inches(8, 5)
        ax.tick_params(labelsize=12, color='lightgrey', labelcolor='lightgrey')
        ax.barh(list(data.keys()), list(data.values()), color='r', height=1.0, linewidth=1, edgecolor='black')
        ax.invert_yaxis()

        plot_bytes = io.BytesIO()
        fig.savefig(
            plot_bytes,
            format='png',
            facecolor='#32363C',
            transparent=True,
            antialiased=True)
        plot_bytes.seek(0)
        fig.clf()

        fname = f"mostactive-{ctx.guild.id}.png"
        plot_file = discord.File(plot_bytes, filename=fname)

        embed = await ctx.embed(
            f"Message Activity Per Member - {ctx.guild.name}", send=False)
        embed.set_image(url=f"attachment://{fname}")
        await ctx.send(file=plot_file, embed=embed)
