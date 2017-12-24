import asyncio
import asyncpg
from discord.ext import commands

PREFIX_SQL = '''SELECT prefix FROM prefix WHERE guild_id=$1;'''


class DatabaseInterface:
    def __init__(self, hostname, username='', password='', port=5432, database="eevee"):
        self.loop = asyncio.get_event_loop()
        self.dsn = "postgres://{}:{}@{}:{}/{}".format(username, password, hostname, port, database)
        self.pool = None
        self.prefix_conn = None
        self.prefix_stmt = None

    async def start(self):
        self.pool = await asyncpg.create_pool(self.dsn)
        self.prefix_conn = await self.pool.acquire()
        self.prefix_stmt = await self.prefix_conn.prepare(PREFIX_SQL)

    async def stop(self):
        if self.prefix_conn:
            await self.pool.release(self.prefix_conn)
            self.prefix_conn = None
            self.prefix_stmt = None
        if self.pool:
            await self.pool.close()
            self.pool.terminate()

    async def execute_query(self, query, *query_args):
        result = []
        async with self.pool.acquire() as conn:
            stmt = await conn.prepare(query)
            rcrds = await stmt.fetch(*query_args)
            for rcrd in rcrds:
                result.append([x for x in rcrd.values()])
        return result

    async def execute_transaction(self, query, *query_args):
        result = []
        async with self.pool.acquire() as conn:
            stmt = await conn.prepare(query)

            if any(isinstance(x, set) for x in query_args):
                async with conn.transaction():
                    for query_arg in query_args:
                        async for rcrd in stmt.cursor(*query_arg):
                            result.append([x for x in rcrd.values()])
            else:
                async with conn.transaction():
                    async for rcrd in stmt.cursor(*query_args):
                        result.append([x for x in rcrd.values()])
            return result

    async def prefix_manager(self, bot, message):
        """Returns the bot prefixes by context.

        Returns a guild-specific prefix if it has been set. If not,
        returns the default prefix.

        Uses a prepared statement to ensure caching.
        """
        default_prefix = bot.default_prefix
        if message.guild:
            guild_prefix = await self.prefix_stmt.fetchval(message.guild.id)
            prefixes = guild_prefix if guild_prefix else default_prefix
        else:
            prefixes = default_prefix

        return commands.when_mentioned_or(*prefixes)(bot, message)
