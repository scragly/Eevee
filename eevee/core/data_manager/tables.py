from eevee.core.data_manager import schema
from eevee.core.logger import LOGGERS

def core_table_sqls():
    sql_dict = {
        'guild_config' : ("CREATE TABLE guild_config ("
                          "guild_id bigint NOT NULL, "
                          "config_name text NOT NULL, "
                          "config_value text NOT NULL, "
                          "CONSTRAINT guild_config_pk "
                          "PRIMARY KEY (guild_id, config_name));"),

        'prefix'       : ("CREATE TABLE prefix ("
                          "guild_id bigint NOT NULL, "
                          "prefix text NOT NULL, "
                          "CONSTRAINT prefixes_pkey "
                          "PRIMARY KEY (guild_id));")
    }

    log_sql = ("CREATE TABLE {log_table} ("
               "log_id bigint NOT NULL, "
               "created bigint NOT NULL, "
               "logger_name text, "
               "level_name text, "
               "file_path text, "
               "module text, "
               "func_name text, "
               "line_no int, "
               "message text, "
               "CONSTRAINT {log_table}_pkey "
               "PRIMARY KEY (log_id));")

    for log in LOGGERS:
        sql_dict[log] = log_sql.format(log_table=log)

    return sql_dict


class CogTable:
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

    def convert_columns(self, columns_dict=None):
        columns = []
        for k, v in columns_dict.items():
            col_cls = v.pop('cls', schema.Column)
            columns.append(col_cls(k, **v))
        return columns

    async def setup(self, table_name=None, columns: list = None, *, primaries=None):
        table_name = table_name or self.table_config["name"]
        table = self.dbi.table(table_name)
        exists = table.exists()
        if not exists:
            columns = self.convert_columns(self.table_config["columns"])
            primaries = primaries or self.table_config["primaries"]
            table = await table.create(
                self.dbi, table_name, columns, primaries=primaries)
        return table
