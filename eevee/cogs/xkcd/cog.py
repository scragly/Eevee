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
        self.update_task = None

    async def get_comic(self, issue: int = None):
        if issue in [404]:
            return None

        url = ISSUE_URL.format(comic_num=issue) if issue else LATEST_URL

        async with timeout(10):
            while True:
                async with self.bot.session.get(url) as r:
                    try:
                        data = await r.json()
                    except aiohttp.ClientResponseError:
                        await asyncio.sleep(1)
                        continue
                    else:
                        return data

    async def latest_id(self):
        data = await self.get_comic()
        return data["num"]

    async def update_data(self, feedback_dest=None):
        if feedback_dest:
            await feedback_dest.send("Starting Update")
        query = self.table.query("id").order_by("id", asc=False).limit(1)
        data = await query.get_one()
        if data:
            result = data["id"]
        else:
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
            update_msg = await feedback_dest.send(update_text + f"\n{result}/{latest} done.")

        for i in range(result+1, latest+1):
            data = await self.get_comic(i)

            if not data:
                continue

            self.table.insert.row(
                id=int(data['num']),
                img=data['img'],
                title=data['title'],
                safe_title=data['safe_title'],
                alt=data['alt'],
                year=int(data['year']),
                month=int(data['month']),
                day=int(data['day']),
                transcript=data['transcript'],
                news=data['news']
            )

            await self.table.insert.commit(do_update=False)

            if feedback_dest:
                last_change = update_msg.edited_at or update_msg.created_at
                since_change = datetime.utcnow() - last_change
                if since_change.total_seconds() > 5:
                    await update_msg.edit(content=update_text + f"\n{data['num']}/{latest} done.")
            await asyncio.sleep(0.1)

        if feedback_dest:
            await update_msg.edit(content=update_text + f"\n{latest}/{latest} done.")
            await feedback_dest.send(f"Updated Complete.")

        self.update_task = None

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

    def cancel_task(self):
        if not self.update_task.done():
            self.update_task.cancel()
        self.update_task = None

    @command()
    async def xkcd_update(self, ctx):
        if self.update_task:
            return await ctx.send("An update is already in progress.")
        self.update_task = ctx.bot.loop.create_task(self.update_data(ctx))

    @command()
    async def xkcd_cancel(self, ctx):
        if not self.update_task:
            return await ctx.send("No update task running.")
        task = self.update_task
        self.cancel_task()
        await ctx.send("Update task cancelled.")
        await task
