# prefix, guild config, raids


class Column:
    def __init__(self, name, data_type="text", required=True):
        self.name = name
        self.data_type = data_type
        self.required = required


class IDColumn(Column):
    def __init__(self, name, required=True):
        super().__init__(name, "bigint", required)


class TextColumn(Column):
    def __init__(self, name, required=True):
        super().__init__(name, "text", required)

class IntColumn(Column):
    def __init__(self, name, required=True):
        super().__init__(name, "int", required)

class BoolColumn(Column):
    def __init__(self, name, required=True):
        super().__init__(name, "bit", required)


class Table:
    """Represents a database table."""

    __slots__ = ('name', 'dbi')

    def __init__(self, name: str, dbi):
        self.name = name
        self.dbi = dbi

    def __str__(self):
        return self.name

    async def get(self, column=None, **filters):
        """Get data from current table."""
        sql = f"SELECT * FROM {self.name}"
        if filters:
            sql += " WHERE"
            multiple = False
            for k, v in kwargs.items():
                if multiple:
                    sql += " AND"
                else:
                    multiple = True
                sql += f" {k}={v}"
        return await self.dbi.execute_query(sql)

    async def get_value(self, column, **filters):
        """Get a column value from current table."""
        await self.get

    @classmethod
    async def create(cls, dbi, name, columns: list, primary: list):
        """Create table and return the object representing it."""
        sql = f"CREATE TABLE {name} ("
        for col in columns:
            collate = " COLLATE" if col.data_type is "text" else ""
            null = " NOT NULL" if col.required else ""
            sql += f"{col.name} {col.data_type}{collate}{null}, "
        sql += f"CONSTRAINT {name}_pkey PRIMARY KEY ({', '.join(primary)}))"
        await dbi.execute_transaction(sql)
        return cls(name, dbi)

    @classmethod
    async def delete(cls, dbi, name):
        """Delete table from database."""
        sql = f"DROP TABLE {name}"
        return await dbi.execute_transaction(sql)
