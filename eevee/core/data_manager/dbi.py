import logging

import asyncpg

from discord.ext.commands import when_mentioned_or

from .schema import Table, TableNew
from .tables import core_table_sqls
from . import sqltypes

class DatabaseInterface:
    """Get, Create and Edit data in the connected database."""

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
        self.types = sqltypes
        self.log = logging.getLogger('eevee.core.dbi.DatabaseInterface')

    async def start(self, loop=None):
        if loop:
            self.loop = loop
        self.pool = await asyncpg.create_pool(self.dsn, loop=loop)
        await self.prepare()

    async def recreate_pool(self):
        self.log.warning(f'Re-creating closed database pool.')
        self.pool = await asyncpg.create_pool(self.dsn, loop=loop)

    async def prepare(self):
        # ensure tables exists
        await self.core_tables_exist()

        # guild prefix callable statement
        self.prefix_conn = await self.pool.acquire()
        prefix_sql = 'SELECT prefix FROM prefix WHERE guild_id=$1;'
        self.prefix_stmt = await self.prefix_conn.prepare(prefix_sql)

        # guild settings statement
        self.settings_conn = await self.pool.acquire()
        settings_sql = ('SELECT config_value FROM guild_config '
                        'WHERE guild_id=$1 AND config_name=$2;')
        self.settings_stmt = await self.settings_conn.prepare(settings_sql)

    async def core_tables_exist(self):
        core_sql = core_table_sqls()
        for k, v in core_sql.items():
            table_exists = await self.table(k).exists()
            if not table_exists:
                self.log.warning(f'Core table {k} not found. Creating...')
                await self.execute_transaction(v)
                self.log.warning(f'Core table {k} created.')

    async def stop(self):
        conns = (self.prefix_conn, self.settings_conn)
        for c in conns:
            if c:
                await self.pool.release(c)
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
        try:
            async with self.pool.acquire() as conn:
                stmt = await conn.prepare(query)
                rcrds = await stmt.fetch(*query_args)
                for rcrd in rcrds:
                    result.append(rcrd)
            return result
        except asyncpg.exceptions.InterfaceError:
            await self.recreate_pool()
            return await self.execute_query(query, *query_args)

    async def execute_transaction(self, query, *query_args):
        result = []
        try:
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
        except asyncpg.exceptions.InterfaceError:
            await self.recreate_pool()
            return await self.execute_query(query, *query_args)

    async def get(self, table: str, columns, **filters):
        """Get data from table based on provided filters.

        Parameters
        -----------
        table: :class:`str`
            Name of the database table
        columns: :class:`str` or :class:`list`, optional
            The columns of data that will be returned
        **filters:
            Remaining keyword arguments will act as a filter for the data
                column_name = record_value: :class:`str`
        """
        if isinstance(columns, (list, set, tuple)):
            columns = ', '.join(columns)
        sql = f"SELECT {columns} FROM {table}"
        if filters:
            filter_list = []
            for i in range(len(filters)):
                filter_list.append(f"{[*filters.keys()][i]}=${i+1}")
            sql += ' WHERE ' + ' AND '.join(filter_list)
        rcrds = await self.execute_query(sql, *filters.values())
        return [dict(r) for r in rcrds]

    async def get_first(self, table: str, columns='*', **filters):
        """Get first record of queried data from table"""
        rcrds = await self.get(table, columns, **filters)
        return rcrds[0] if rcrds else None

    async def get_value(self, table: str, column: str, **filters):
        """Get first record value of queried data from table"""
        rcrd = await self.get_first(table, column, **filters)
        return list(rcrd.values())[0] if rcrd else None

    async def get_values(self, table: str, column: str = '*', **filters):
        """Get first record value of queried data from table"""
        rcrds = await self.get(table, column, **filters)
        return [list(r.values())[0] for r in rcrds] if rcrds else None

    async def insert(self, table: str, **data):
        """Add records to a table."""
        column = ', '.join(data.keys())
        col_idx = ', '.join([f'${i+1}' for i in range(len(data))])
        sql = f"INSERT INTO {table} ({column}) VALUES ({col_idx})"
        return await self.execute_transaction(sql, *data.values())

    async def upsert(self, table: str, primary=None, **data):
        """Add or update records of a table."""
        column = ', '.join(data.keys())
        col_idx = ', '.join([f'${i+1}' for i in range(len(data))])
        sql = f"INSERT INTO {table} ({column}) VALUES ({col_idx})"
        if not primary:
            primary = await self.get_table_primary(table)
        if isinstance(primary, (list, tuple)):
            primary = ', '.join(primary)
        sql += f" ON CONFLICT ({primary}) DO UPDATE SET "
        excluded = [f'{c} = excluded.{c}' for c in data]
        sql += f"{', '.join(excluded)};"
        return await self.execute_transaction(sql, *data.values())

    async def delete(self, table: str, **filters):
        """Deletes records from table."""
        filter_list = []
        for i in range(len(filters)):
            filter_list.append(f"{[*filters.keys()][i]}=${i+1}")
        sql = f"DELETE FROM {table} WHERE {' AND '.join(filter_list)}"
        return await self.execute_transaction(sql, *filters.values())

    async def create_table(self, name, columns: list, *, primaries=None):
        """Create table."""
        return await Table(self, name).create(columns, primaries=primaries)

    async def delete_table(self, name):
        """Delete table."""
        return await Table(name).drop()

    async def get_table_columns(self, table):
        """Get column from table."""
        return await self.get_values('information_schema.columns',
                                     'column_name', TABLE_NAME=table)

    async def get_table_primary(self, table):
        """Get column from table."""
        return await self.get_values('information_schema.key_column_usage',
                                     'column_name', TABLE_NAME=table)

    def table(self, name):
        return Table(name, self)

    def tablenew(self, name):
        return TableNew(name, self)

    def query(self, table_name):
        return TableNew(table_name, self).query
