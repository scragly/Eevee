import discord

from eevee import command, checks, utils

class Tests:
    """Test Features"""

    def __init__(self, bot):
        self.bot = bot

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
    async def embed_test(self, ctx, title=None, content=None, msg_type='', colour=None, icon_url=None):
        embed = utils.make_embed(
            msg_type=msg_type, title=title, content=content,
            msg_colour=colour, guild=ctx.guild, icon=icon_url)
        await ctx.send(embed=embed)

    @command()
    async def cattest(self, ctx, category):
        try:
            if command is None:
                p = await HP.from_bot(ctx)
            else:
                p = await HP.from_category(ctx, category)

            await p.paginate()
        except Exception as e:
            await ctx.send(e)

    @command()
    async def test(self, ctx):
        await ctx.send(ctx.author)

    def __local_check(self, ctx):
        return checks.check_is_co_owner(ctx)

    @command()
    async def aemoji(self, ctx):
        """Run a command as a different member."""
        await ctx.send("<a:ablobunamused:393721462634184705>")

    @command()
    async def getemoji(self, ctx):
        """Run a command as a different member."""
        await ctx.send(str(ctx.guild.emojis))
