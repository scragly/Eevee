from eevee.core.data_manager import schema


def setup(bot):
    table = bot.dbi.table('xkcd')
    table.new_columns = [
        schema.IntColumn('id', primary_key=True),
        schema.StringColumn('img'),
        schema.StringColumn('title'),
        schema.StringColumn('safe_title'),
        schema.StringColumn('alt'),
        schema.IntColumn('year'),
        schema.IntColumn('month'),
        schema.IntColumn('day'),
        schema.StringColumn('transcript'),
        schema.StringColumn('news')
    ]
    return table
