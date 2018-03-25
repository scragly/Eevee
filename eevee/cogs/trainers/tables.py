from eevee.core.data_manager import schema

def setup(bot):
    cog_table = bot.dbi.table('trainers')
    cog_table.new_columns = [
        schema.IDColumn('trainer_id', primary_key=True),
        schema.StringColumn('silph_id'),
        schema.IntColumn('pokebattler_id'),
        schema.IntColumn('team', small=True)
        ]
    return cog_table
