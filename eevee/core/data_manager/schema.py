from .errors import PostgresError, SchemaError, ResponseError, QueryError
from .sqltypes import (BooleanSQL, DatetimeSQL, DecimalSQL, IntegerSQL,
                       IntervalSQL, SQLType, StringSQL)

class SQLOperator:

    default_template = '{column} {operator} {value}'

    def __init__(self, sql_operator, python_operator, str_template):
        self.sql = sql_operator
        self.python = python_operator
        self.template = str_template

    def __str__(self):
        return self.sql

    def format(self, **kwargs):
        return self.template.format(operator=self.sql, **kwargs)

    @classmethod
    def lt(cls):
        return cls('<', '<', cls.default_template)

    @classmethod
    def le(cls):
        return cls('<=', '<', cls.default_template)

    @classmethod
    def eq(cls):
        return cls('=', '==', cls.default_template)

    @classmethod
    def ne(cls):
        return cls('!=', '!=', cls.default_template)

    @classmethod
    def gt(cls):
        return cls('>', '>', cls.default_template)

    @classmethod
    def ge(cls):
        return cls('>=', '>=', cls.default_template)

    @classmethod
    def like(cls):
        return cls('~~', None, cls.default_template)

    @classmethod
    def ilike(cls):
        return cls('~~*', None, cls.default_template)

    @classmethod
    def not_like(cls):
        return cls('!~~', None, cls.default_template)

    @classmethod
    def not_ilike(cls):
        return cls('!~~*', None, cls.default_template)

    @classmethod
    def between(cls):
        return cls(
            'BETWEEN', None, '{column} {operator} {minvalue} AND {maxvalue}')

    @classmethod
    def in_(cls):
        return cls('IN', 'in', cls.default_template)

    @classmethod
    def is_(cls):
        return cls('IS', 'is', cls.default_template)


class SQLComparison:
    def __init__(self, operator, aggregate, column, value=None,
                 minvalue=None, maxvalue=None):
        self.operator = operator
        self.format = operator.format
        self.aggregate = aggregate
        self._column = column
        self.value = value
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    @property
    def column(self):
        if self.aggregate:
            return f"{self.aggregate}({self._column})"
        else:
            return str(self._column)

    def __str__(self):
        return self.operator.format(
            column=self.column, value=self.value,
            minvalue=self.minvalue, maxvalue=self.maxvalue)


class Column:
    __slots__ = ('name', 'data_type', 'primary_key', 'required',
                 'default', 'unique', 'table', 'aggregate')

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
        self.aggregate = None

    def __str__(self):
        if self.aggregate:
            return f"{self.aggregate} ({self.name})"
        else:
            return self.name

    def __lt__(self, value):
        return SQLComparison(
            SQLOperator.lt(), self.aggregate, self.name, value)

    def __le__(self, value):
        return SQLComparison(
            SQLOperator.le(), self.aggregate, self.name, value)

    def __eq__(self, value):
        return SQLComparison(
            SQLOperator.eq(), self.aggregate, self.name, value)

    def __ne__(self, value):
        return SQLComparison(
            SQLOperator.ne(), self.aggregate, self.name, value)

    def __gt__(self, value):
        return SQLComparison(
            SQLOperator.gt(), self.aggregate, self.name, value)

    def __ge__(self, value):
        return SQLComparison(
            SQLOperator.ge(), self.aggregate, self.name, value)

    def like(self, value):
        return SQLComparison(
            SQLOperator.like(), self.aggregate, self.name, value)

    def ilike(self, value):
        return SQLComparison(
            SQLOperator.ilike(), self.aggregate, self.name, value)

    def not_like(self, value):
        return SQLComparison(
            SQLOperator.not_like(), self.aggregate, self.name, value)

    def not_ilike(self, value):
        return SQLComparison(
            SQLOperator.not_ilike(), self.aggregate, self.name, value)

    def between(self, minvalue, maxvalue):
        return SQLComparison(
            SQLOperator.between(), self.aggregate, self.name,
            minvalue=minvalue, maxvalue=maxvalue)

    def in_(self, value):
        return SQLComparison(
            SQLOperator.in_(), self.aggregate, self.name, value)

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

    @property
    def count(self):
        self.aggregate = 'COUNT'
        return self

    @property
    def sum(self):
        self.aggregate = 'SUM'
        return self

    @property
    def avg(self):
        self.aggregate = 'AVG'
        return self

    @property
    def min(self):
        self.aggregate = 'MIN'
        return self

    @property
    def max(self):
        self.aggregate = 'MAX'
        return self

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

class TableNew:
    """Represents a database table."""

    __slots__ = ('name', 'dbi', 'columns', '_filters', 'new_columns',
                 'query')

    def __init__(self, name: str, dbi):
        self.name = name
        self.dbi = dbi
        self._filters = {}
        self.columns = TableColumns(self)
        self.new_columns = []
        self.query = Query(dbi, self.name)

    def __str__(self):
        return self.name

    async def _get_columns(self):
        return await self.dbi.get_table_columns(self.name)

    async def _get_primary(self):
        return self.dbi.get_table_primary(self.name)

    async def insert(self, **data):
        """Add record to current table."""
        data = dict(self._filters, **data)
        return await self.dbi.insert(self.name, **data)

    async def upsert(self, **data):
        """Add record to current table."""
        data = dict(self._filters, **data)
        return await self.dbi.upsert(self.name, **data)

    async def delete(self, **filters):
        """Deletes records from the current table."""
        filters = dict(self._filters, **filters)
        return await self.dbi.delete(self.name, **filters)

    @classmethod
    def create_sql(cls, name, *columns, primaries=None):
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


class SQLConditions:
    def __init__(self, query=None, having=False):
        self.having = having
        self.query = query
        if having:
            self.add_cond = query.add_having
        else:
            self.add_cond = query.add_conditions

    def and_(self, *conditions):
        self.add_cond(*conditions)
        return self.query

    __call__ = and_

    def or_(self, *conditions):
        self.add_cond(conditions)
        return self.query


class Query:
    """Builds a database query."""
    def __init__(self, dbi, table=None):
        self._dbi = dbi
        self._select = []
        self._conditions = tuple()
        self._having = tuple()
        self._distinct = False
        self._group_by = []
        self._order_by = []
        self._sort = ''
        self._from = (table,) if table else set()
        self._limit = None
        self._offset = None
        self.where = SQLConditions(query=self)
        self.having = SQLConditions(query=self, having=True)
        self._value_count = 0

    def select(self, *columns):
        self._select = []
        self._distinct = False
        for col in columns:
            if isinstance(col, Column):
                self._select.append(col.name)
                if not self._from and col.table:
                    self._from.add(col.table.name)
            elif isinstance(col, str):
                self._select.append(col)
        return self

    __call__ = select

    def clear_conditions(self):
        self._conditions = tuple()
        self._having = tuple()
        return self

    def add_conditions(self, *conditions):
        con = []
        hav = []
        for c in conditions:
            if not isinstance(c, tuple):
                if c.aggregate:
                    hav.append(c)
                else:
                    con.append(c)
            else:
                con.append(c)
        self._conditions = (*self._conditions, *con)
        self._having = (*self._having, *hav)
        return self

    def add_having(self, *conditions):
        self._having = (*self._conditions, *conditions)
        return self

    def select_distinct(self, *columns):
        self._select = []
        self._distinct = True
        for col in columns:
            if isinstance(col, Column):
                self._select.append(col.name)
                if not self._from and col.table:
                    self._from.add(col.table.name)
            elif isinstance(col, str):
                self._select.append(col)
        return self

    def table(self, *tables):
        self._from = set()
        for table in tables:
            if isinstance(table, Table):
                self._from.add(table.name)
            elif isinstance(table, str):
                self._from.add(table)
        return self

    def group_by(self, *columns):
        for col in columns:
            if isinstance(col, Column):
                self._group_by.append(col.name)
            elif isinstance(col, str):
                self._group_by.append(col)
        return self

    def order_by(self, *columns, asc: bool = None):
        if asc is False:
            self._sort = 'DESC'
        if asc is True:
            self._sort = 'ASC'
        if asc is None:
            self._sort = ''
        for col in columns:
            if isinstance(col, Column):
                self._order_by.append(col.name)
            elif isinstance(col, str):
                self._order_by.append(col)
        return self

    def limit(self, number=None):
        if not isinstance(number, (int, type(None))):
            raise TypeError("Method 'limit' only accepts an int argument.")
        self._limit = number
        return self

    def offset(self, number=None):
        if not isinstance(number, (int, type(None))):
            raise TypeError("Method 'limit' only accepts an int argument.")
        self._offset = number
        return self

    @property
    def _count(self):
        self._value_count += 1
        return self._value_count

    def _build_conditions(self, *conditions):
        con_sql = []
        values = []
        for condition in conditions:
            if isinstance(condition, tuple):
                c, v = self._build_conditions(*condition)
                con_str = f"({' OR '.join(c)})"
                con_sql.append(con_str)
                values.extend(v)
            else:
                data = dict(column=condition.column)
                if condition.value is not None:
                    data.update(value=f"${self._count}")
                    values.append(condition.value)
                else:
                    data.update(minvalue=f"${self._count}")
                    values.append(condition.minvalue)
                    data.update(maxvalue=f"${self._count}")
                    values.append(condition.maxvalue)
                con_str = condition.format(**data)
                con_sql.append(con_str)
        return (con_sql, values)

    @property
    def sql(self):
        query_values = []
        sql = []
        select_str = "SELECT"
        if self._distinct:
            select_str = "SELECT DISTINCT"
        if not self._select:
            sql.append(f"{select_str} *")
        else:
            select_names = [str(c) for c in self._select]
            sql.append(f"{select_str} {', '.join(select_names)}")
        sql.append(f"FROM {', '.join(self._from)}")
        if self._conditions:
            con_sql, values = self._build_conditions(*self._conditions)
            query_values.extend(values)
            sql.append(f"WHERE {' AND '.join(con_sql)}")
        if self._group_by:
            sql.append(f"GROUP BY {', '.join(self._group_by)}")
        if self._having:
            con_sql, values = self._build_conditions(*self._having)
            query_values.extend(values)
            sql.append(f"HAVING {' AND '.join(con_sql)}")
        if self._order_by:
            sort_str = f" {self._sort}" if self._sort else ''
            sql.append(f"ORDER BY {', '.join(self._order_by)}{sort_str}")
        if self._limit:
            sql.append(f"LIMIT {self._limit}")
        if self._offset:
            sql.append(f"OFFSET {self._offset}")
        return (f"{' '.join(sql)};", query_values)

    async def get(self):
        query, args = self.sql
        return await self._dbi.execute_query(query, *args)

    async def get_one(self):
        old_limit = self._limit
        self.limit(2)
        data = await self.get()
        self.limit(old_limit)
        if len(data) > 1:
            raise ResponseError('More than one result returned.')
        return data

    async def get_first(self):
        old_limit = self._limit
        self.limit(1)
        data = await self.get()
        self.limit(old_limit)
        return data

    async def get_value(self):
        if len(self._select) == 1:
            data = await self.get_one()
            return next(data[0].values())
        else:
            raise QueryError("Query doesn't have a single column selected.")

    async def get_values(self):
        if len(self._select) == 1:
            data = await self.get()
            return [next(row.values()) for row in data]
        else:
            raise QueryError("Query doesn't have a single column selected.")
