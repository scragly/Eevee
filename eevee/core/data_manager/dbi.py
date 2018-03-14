import asyncio
import asyncpg
from discord.ext.commands import when_mentioned_or
from .schema import Table
from . import types

class DatabaseInterface:
    def __init__(self,
                 password,
                 hostname='localhost',
                 username='eevee',
                 database="eevee",
                 port=5432):
        self.loop = None
        self.dsn = "postgres://{}:{}@{}:{}/{}".format(
            username, password, hostname, port, database)
        self.pool = None
        self.prefix_conn = None
        self.prefix_stmt = None
        self.settings_conn = None
        self.settings_stmt = None
        self.types = types

    async def start(self, loop=None):
        if loop:
            self.loop = loop
        self.pool = await asyncpg.create_pool(self.dsn, loop=loop)
        self.prefix_conn = await self.pool.acquire()
        self.settings_conn = await self.pool.acquire()
        prefix_sql = 'SELECT prefix FROM prefix WHERE guild_id=$1;'
        settings_sql = ('SELECT config_value FROM guild_config '
                        'WHERE guild_id=$1 AND config_name=$2;')
        self.prefix_stmt = await self.prefix_conn.prepare(prefix_sql)
        self.settings_stmt = await self.settings_conn.prepare(settings_sql)

    async def stop(self):
        if self.prefix_conn:
            await self.pool.release(self.prefix_conn)
            self.prefix_conn = None
            self.prefix_stmt = None
        if self.pool:
            await self.pool.close()
            self.pool.terminate()

    async def prefix_manager(self, bot, message):
        """Returns the bot prefixes by context.

        Returns a guild-specific prefix if it has been set. If not,
        returns the default prefix.

        Uses a prepared statement to ensure caching.
        """
        default_prefix = bot.default_prefix
        if message.guild:
            g_prefix = await self.prefix_stmt.fetchval(message.guild.id)
            prefix = g_prefix if g_prefix else default_prefix
        else:
            prefix = default_prefix

        return when_mentioned_or(prefix)(bot, message)

    async def execute_query(self, query, *query_args):
        result = []
        async with self.pool.acquire() as conn:
            stmt = await conn.prepare(query)
            rcrds = await stmt.fetch(*query_args)
            for rcrd in rcrds:
                result.append(rcrd)
        return result

    async def execute_transaction(self, query, *query_args):
        result = []
        async with self.pool.acquire() as conn:
            stmt = await conn.prepare(query)

            if any(isinstance(x, (set, tuple)) for x in query_args):
                async with conn.transaction():
                    for query_arg in query_args:
                        async for rcrd in stmt.cursor(*query_arg):
                            result.append(rcrd)
            else:
                async with conn.transaction():
                    async for rcrd in stmt.cursor(*query_args):
                        result.append(rcrd)
            return result

    async def get(self, table_name: str, col_name: str, **filters):
        """Get all records from filtered table."""
        sql = f"SELECT {col_name} FROM {table_name}"
        if filters:
            filter_list = []
            for i in range(len(filters)):
                filter_list.append(f"{[*filters.keys()][i]}=${i+1}")
            sql += ' WHERE ' + ' AND '.join(filter_list)
        return await self.execute_query(sql, *filters.values())

    async def get_first(self, table_name: str, col_name: str = '*', **filters):
        """Get first record of queried data from table"""
        rcrds = await self.get(table_name, col_name, **filters)
        return rcrds[0] if rcrds else None

    async def get_value(self, table_name: str, col_name: str, **filters):
        """Get first record value of queried data from table"""
        rcrd = await self.get_first(table_name, col_name, **filters)
        return rcrd[0] if rcrd else None

    async def get_values(self, table_name: str, col_name: str = '*', **filters):
        """Get first record value of queried data from table"""
        rcrds = await self.get(table_name, col_name, **filters)
        return [r[0] for r in rcrds] if rcrds else None

    async def insert(self, table_name: str, columns: list, *values):
        """Add records to a table."""
        col_name = ', '.join(columns)
        col_idx = ', '.join([f'${i+1}' for i in range(len(columns))])
        sql = f"INSERT INTO {table_name} ({col_name}) VALUES ({col_idx})"
        return await self.execute_transaction(sql, *values)

    async def upsert(self, table_name: str, primary, columns: list, *values):
        """Add or update records of a table."""
        col_names = ', '.join(columns)
        col_idx = ', '.join([f'${i+1}' for i in range(len(columns))])
        sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({col_idx})"
        primary = ', '.join(primary) if isinstance(
            primary, (list, tuple)) else primary
        sql += f" ON CONFLICT ({primary}) DO UPDATE SET"
        excluded = [f' {c} = excluded.{c}' for c in columns]
        sql += f"{', '.join(excluded)};"
        return await self.execute_transaction(sql, *values)

    async def delete(self, table_name: str, **filters):
        """Deletes records from table."""
        filter_list = []
        for i in range(len(filters)):
            filter_list.append(f"{[*filters.keys()][i]}=${i+1}")
        sql = f"DELETE FROM {table_name} WHERE {' AND '.join(filter_list)}"
        return await self.execute_transaction(sql, *filters.values())

    async def create_table(self, name, columns: list, *, primaries=None):
        """Create table."""
        return await Table.create(self, name, columns, primaries=primaries)

    async def delete_table(self, name):
        """Delete table."""
        return await Table.drop(self, name)

    async def get_table_columns(self, table_name):
        """Get column from table."""
        return await self.get_values('information_schema.columns',
                                     'column_name', TABLE_NAME=table_name)

    async def get_table_primary(self, table_name):
        """Get column from table."""
        return await self.get_values('information_schema.key_column_usage',
                                     'column_name', TABLE_NAME=table_name)

    def table(self, table_name):
        return Table(table_name, self)
