from .errors import PostgresError, SchemaError
from .types import (BooleanSQL, DatetimeSQL, DecimalSQL, IntegerSQL,
                    IntervalSQL, SQLType, StringSQL)


class Column:
    __slots__ = ('name', 'data_type', 'primary_key', 'required',
                 'default', 'unique', 'table')

    def __init__(self, name, data_type=None, *, primary_key=False,
                 required=False, default=None, unique=False, table=None):
        self.name = name
        if data_type:
            if not isinstance(data_type, SQLType):
                raise TypeError('Data types must be SQLType.')
        self.data_type = data_type
        self.primary_key = primary_key
        self.required = required
        self.default = default
        self.unique = unique
        if sum(map(bool, [primary_key, default is not None, unique])) > 1:
            raise SchemaError('Set only one of either primary_key, default or '
                              'unique')
        self.table = table

    def __str__(self):
        return self.name

    @classmethod
    def from_dict(cls, data):
        name = data.pop('name')
        data_type = data.pop('data_type')
        data_type = SQLType.from_dict(data_type)
        return cls(name, data_type, **data)

    @property
    def to_sql(self):
        sql = []
        sql.append(self.name)
        sql.append(self.data_type.to_sql())
        if self.default is not None:
            if isinstance(self.default, str) and isinstance(self.data_type, str):
                default = f"'{self.default}'"
            elif isinstance(self.default, bool):
                default = str(default).upper()
            else:
                default = f"{self.default}"
            sql.append(default)
        elif self.unique:
            sql.append('UNIQUE')
        elif self.primary_key:
            sql.append('PRIMARY KEY')
        if self.required:
            sql.append('NOT NULL')
        return ' '.join(sql)

    async def set(self, value):
        if not self.table:
            return None
        data = dict(self.table.current_filter)
        data[self.name] = value
        return await self.table.upsert(**data)

    async def get(self, **filters):
        return await self.table.get(columns=self.name, **filters)

    async def get_first(self, **filters):
        return await self.table.get_first(column=self.name, **filters)


class IDColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, IntegerSQL(big=True), **kwargs)

class StringColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, StringSQL(), **kwargs)

class IntColumn(Column):
    def __init__(self, name, big=False, small=False, **kwargs):
        super().__init__(name, IntegerSQL(big=big, small=small), **kwargs)

class BoolColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, BooleanSQL(), **kwargs)

class DatetimeColumn(Column):
    def __init__(self, name, *, timezone=False, **kwargs):
        super().__init__(name, DatetimeSQL(timezone=timezone), **kwargs)

class DecimalColumn(Column):
    def __init__(self, name, *, precision=None, scale=None, **kwargs):
        super().__init__(
            name, DecimalSQL(precision=precision, scale=scale), **kwargs)

class IntervalColumn(Column):
    def __init__(self, name, field=False, **kwargs):
        super().__init__(name, IntervalSQL(field), **kwargs)

class TableColumns:
    def __init__(self, table):
        self._table = table
    def __getattr__(self, name):
        return Column(name, table=self._table)

class Table:
    """Represents a database table."""

    __slots__ = ('name', 'dbi', 'columns', 'current_filter', 'new_columns')

    def __init__(self, name: str, dbi):
        self.name = name
        self.dbi = dbi
        self.current_filter = {}
        self.columns = TableColumns(self)
        self.new_columns = []

    def __str__(self):
        return self.name

    def where(self, **filters):
        if filters:
            self.current_filter = filters
            return self
        return self.current_filter

    def clear_filter(self):
        self.current_filter = {}

    async def _get_columns(self):
        return await self.dbi.get_table_columns(self.name)

    async def _get_primary(self):
        return self.dbi.get_table_primary(self.name)

    async def get(self, columns='*', **filters):
        """Returns values from columns of filtered table."""
        filters = dict(self.current_filter, **filters)
        return await self.dbi.get(self.name, columns, **filters)

    async def get_values(self, column='*', **filters):
        """Returns list of values in a column from filtered table."""
        filters = dict(self.current_filter, **filters)
        return await self.dbi.get_values(self.name, column, **filters)

    async def get_value(self, column, **filters):
        """Returns a single value from a column from filtered table."""
        filters = dict(self.current_filter, **filters)
        return await self.dbi.get_value(self.name, column, **filters)

    async def get_first(self, columns='*', **filters):
        """Returns first row from filtered table."""
        filters = dict(self.current_filter, **filters)
        return await self.dbi.get_first(self.name, columns, **filters)

    async def insert(self, **data):
        """Add record to current table."""
        data = dict(self.current_filter, **data)
        return await self.dbi.insert(self.name, **data)

    async def upsert(self, **data):
        """Add record to current table."""
        data = dict(self.current_filter, **data)
        return await self.dbi.upsert(self.name, **data)

    async def delete(self, **filters):
        """Deletes records from the current table."""
        filters = dict(self.current_filter, **filters)
        return await self.dbi.delete(self.name, **filters)

    @classmethod
    def test_create(cls, name, *columns, primaries=None):
        """Generate SQL for creating the table."""
        sql = f"CREATE TABLE {name} ("
        sql += ', '.join(col.to_sql for col in columns)
        if primaries:
            if isinstance(primaries, str):
                sql += f", CONSTRAINT {name}_pkey PRIMARY KEY ({primaries})"
            elif isinstance(primaries, (list, tuple, set)):
                sql += (f", CONSTRAINT {name}_pkey"
                        f" PRIMARY KEY ({', '.join(primaries)}))")
        sql += ")"
        return sql

    async def create(self, *columns, primaries=None):
        """Create table and return the object representing it."""
        sql = f"CREATE TABLE {self.name} ("
        if not columns:
            if not self.new_columns:
                raise SchemaError("No columns for created table.")
            columns = self.new_columns
        sql += ', '.join(col.to_sql for col in columns)
        if primaries:
            if isinstance(primaries, str):
                sql += f", CONSTRAINT {self.name}_pkey PRIMARY KEY ({primaries})"
            elif isinstance(primaries, (list, tuple, set)):
                sql += (f", CONSTRAINT {self.name}_pkey"
                        f" PRIMARY KEY ({', '.join(primaries)}))")
        sql += ")"
        try:
            await self.dbi.execute_transaction(sql)
        except PostgresError:
            raise
        else:
            return self

    async def exists(self):
        """Create table and return the object representing it."""
        sql = f"SELECT to_regclass('{self.name}')"
        try:
            result = await self.dbi.execute_query(sql)
        except PostgresError:
            raise
        else:
            return bool(list(result[0])[0])

    @classmethod
    async def drop(cls, dbi, name):
        """Drop table from database."""
        sql = f"DROP TABLE {name}"
        return await dbi.execute_transaction(sql)
