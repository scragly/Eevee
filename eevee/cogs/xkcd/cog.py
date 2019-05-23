import asyncio
from datetime import datetime

import aiohttp
from async_timeout import timeout

from eevee import command, Cog

LATEST_URL = "https://xkcd.com/info.0.json"
ISSUE_URL = "https://xkcd.com/{comic_num}/info.0.json"


class XKCD(Cog):
    """Test commands that are open for public usage."""
    def __init__(self, bot):
        self.bot = bot
        self.table = bot.dbi.table('xkcd')

    async def get_comic(self, issue: int = None):
        url = ISSUE_URL.format(comic_num=issue) if issue else LATEST_URL
        async with self.bot.session.get(url) as r:
            return await r.json()

    async def latest_id(self):
        data = await self.get_comic()
        return data["num"]

    async def update_data(self, feedback_dest=None):
        if feedback_dest:
            await feedback_dest.send("Starting Update")
        query = self.table.query("id").order_by("id", asc=False).limit(1)
        result = await query.get_one()
        if not result:
            result = 0

        if feedback_dest:
            await feedback_dest.send(f"Latest Stored Comic ID: {result}")

        latest = await self.latest_id()
        if feedback_dest:
            await feedback_dest.send(f"Latest Released Comic ID: {latest}")

        if result >= latest:
            if feedback_dest:
                await feedback_dest.send(f"Update Finished: No new releases found.")
            return

        if feedback_dest:
            update_text = f"Pulling updates for comics {result} to {latest}."
            update_msg = await feedback_dest.send(update_text + f"\n0/{latest} collected.")

        for i in range(result+1, latest+1):
            try:
                data = await self.get_comic(i)
            except aiohttp.ContentTypeError:
                if feedback_dest:
                    await feedback_dest.send(f"Comic {i} failed.")
                await asyncio.sleep(1)
                continue

            self.table.insert.row(
                id=data['num'],
                img=data['img'],
                title=data['title'],
                safe_title=data['safe_title'],
                alt=data['alt'],
                year=data['year'],
                month=data['month'],
                day=data['day'],
                transcript=data['transcript'],
                news=data['news']
            )

            if feedback_dest:
                last_change = update_msg.edited_at or update_msg.created_at
                since_change = datetime.utcnow() - last_change
                if since_change.total_seconds() > 5:
                    await update_msg.edit(content=update_text + f"\n{data['num']}/{latest} collected.")
            await asyncio.sleep(0.1)

        if feedback_dest:
            await update_msg.edit(content=update_text + f"\n{latest}/{latest} collected.")

        self.table.insert.commit(do_update=False)

        if feedback_dest:
            await feedback_dest.send(f"Updated Data Saved.")

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

    @command()
    async def xkcd_update(self, ctx):
        await self.update_data(ctx)
