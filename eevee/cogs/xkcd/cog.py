from async_timeout import timeout

from eevee import command, Cog


class XKCD(Cog):
    """Test commands that are open for public usage."""
    def __init__(self, bot):
        self.bot = bot

    @command()
    async def xkcd(self, ctx, comic_number: int = None):
        url_num = f"{comic_number}/" if comic_number else ""
        url = f"https://xkcd.com/{url_num}info.0.json"
        async with timeout(10):
            async with ctx.bot.session.get(url) as response:
                xkcd_data = await response.json()
        title = (f"{xkcd_data['safe_title']} - "
                 f"{xkcd_data['num']} - "
                 f"{xkcd_data['year']}/{xkcd_data['month']}/{xkcd_data['day']}")
        await ctx.embed(title, footer=xkcd_data['alt'], image=xkcd_data['img'])
