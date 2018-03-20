from eevee.core.data_manager import schema

CORE_TABLE_SQL = """
CREATE TABLE guild_config
(
    guild_id bigint NOT NULL,
    config_name text NOT NULL,
    config_value text NOT NULL,
    CONSTRAINT guild_config_pk PRIMARY KEY (guild_id, config_name)
);
CREATE TABLE prefix
(
    guild_id bigint NOT NULL,
    prefix text NOT NULL,
    CONSTRAINT prefixes_pkey PRIMARY KEY (guild_id)
); 
"""


class CogTables:

    table_config = {
        "name" : "base_default_table",
        "columns" : {
            "id" : {"cls" : schema.IDColumn},
            "value" : {"cls" : schema.StringColumn}
        },
        "primaries" : ("id")
    }

    def __init__(self, bot):
        self.dbi = bot.dbi
        self.bot = bot
        self.tables = []

    def convert_columns(self, columns_dict=None):
        columns = []
        for k, v in columns_dict.items():
            col_cls = v.pop('cls', schema.Column)
            columns.append(col_cls(k, **v))
        return columns

    async def setup(self, table_name=None, columns: list = None, *, primaries=None):
        table_name = table_name or self.table_config["name"]
        columns = self.convert_columns(self.table_config["columns"])
        primaries = primaries or self.table_config["primaries"]
        table = await self.dbi.Table.create(
            self.dbi, table_name, columns, primaries=primaries)
        self.tables.append(table)
