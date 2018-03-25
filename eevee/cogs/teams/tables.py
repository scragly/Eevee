from eevee.core.data_manager import schema

def setup(bot):
    cog_table = bot.dbi.table('teams')
    cog_table.new_columns = [
        schema.IntColumn('team_id', small=True, primary_key=True),
        schema.IntColumn('lang_id', small=True, primary_key=True),
        schema.StringColumn('team_name')
        ]
    return cog_table
