from .types import (SQLType, StringSQL, BooleanSQL, DatetimeSQL,
                    IntegerSQL, DecimalSQL, IntervalSQL)
from .errors import SchemaError, PostgresError


class Column:
    __slots__ = ('name', 'data_type', 'primary_key', 'required', 'value',
                 'default', 'unique')

    def __init__(self, name, data_type, *, primary_key=False,
                 required=False, value=None, default=None, unique=False):
        self.name = name
        if not isinstance(data_type, SQLType):
            raise TypeError('Data types must be SQLType.')
        self.data_type = data_type
        self.primary_key = primary_key
        self.required = required
        self.value = value
        self.default = default
        self.unique = unique
        if sum(map(bool, [primary_key, default is not None, unique])) > 1:
            raise SchemaError('Set only one of either primary_key, default or '
                              'unique')

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
            if isinstance(self.default, str) and (self.data_type, String):
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

class IDColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, IntegerSQL(big=True), **kwargs)

class StringColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, StringSQL(), **kwargs)

class IntColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, IntegerSQL(), **kwargs)

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

class Table:
    """Represents a database table."""

    __slots__ = ('name', 'dbi')

    def __init__(self, name: str, dbi):
        self.name = name
        self.dbi = dbi

    def __str__(self):
        return self.name

    def _get_columns(self):
        return self.dbi.get_table_columns(self, self.name)

    async def get(self, column='*', **filters):
        """Get data from current table."""
        return await self.dbi.get(self.name, str(column), **filters)

    async def get_first(self, column='*', **filters):
        """Get first matching record from current table."""
        return await self.dbi.get_first(self.name, str(column), **filters)

    async def get_value(self, column, **filters):
        """Get matching record value from current table."""
        return await self.dbi.get_value(self.name, str(column), **filters)

    async def get_values(self, column, **filters):
        """Get matching record value from current table."""
        return await self.dbi.get_values(self.name, str(column), **filters)

    async def insert(self, data):
        """Add record to current table."""
        if isinstance(data, dict):
            return await self.dbi.insert(
                self, self.name, [*data.keys()], *data.values())
        elif isinstance(data, (set, list, tuple)):
            columns = await self.dbi.get_table_columns(self.name)
            return await self.dbi.insert(self.name, columns, *data)
        else:
            raise SchemaError(
                'Data to be added must be dict, list, tuple or set.')

    async def upsert(self, data):
        """Add record to current table."""
        if isinstance(data, dict):
            return await self.dbi.insert(
                self, self.name, [*data.keys()], *data.values())
        elif isinstance(data, (set, list, tuple)):
            keys = await self.dbi.get_table_primary(self.name)
            columns = await self.dbi.get_table_columns(self.name)
            return await self.dbi.upsert(self.name, keys, columns, *data)
        else:
            raise SchemaError(
                'Data to be added must be dict, list, tuple or set.')

    async def delete(self, **filters):
        """Deletes records from the current table."""
        return await self.dbi.delete(self.name, **filters)

    @classmethod
    def _test_create(cls, name, columns: list, *, primaries=None):
        """Generate SQL for creating the table."""
        sql = f"CREATE TABLE {name} ("
        sql += ', '.join(col.to_sql for col in columns)
        if primaries:
            if isinstance(primaries, str):
                sql += f"CONSTRAINT {name}_pkey PRIMARY KEY (primaries)"
            elif isinstance(primaries, (list, tuple, set)):
                sql += (f"CONSTRAINT {name}_pkey "
                        f"PRIMARY KEY ({', '.join(primaries)}))")
        sql += ")"
        return sql

    @classmethod
    async def create(cls, dbi, name, columns: list, *, primaries=None):
        """Create table and return the object representing it."""
        sql = f"CREATE TABLE {name} ("
        sql += ', '.join(col.to_sql for col in columns)
        if primaries:
            if isinstance(primaries, str):
                sql += f"CONSTRAINT {name}_pkey PRIMARY KEY (primaries)"
            elif isinstance(primaries, (list, tuple, set)):
                sql += (f"CONSTRAINT {name}_pkey "
                        f"PRIMARY KEY ({', '.join(primaries)}))")
        sql += ")"
        try:
            await dbi.execute_transaction(sql)
        except PostgresError:
            raise
        else:
            return cls(name, dbi)

    @classmethod
    async def drop(cls, dbi, name):
        """Drop table from database."""
        sql = f"DROP TABLE {name}"
        return await dbi.execute_transaction(sql)
