from asyncpg import PostgresError

class SchemaError(PostgresError):
    pass
