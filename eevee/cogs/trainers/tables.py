from eevee.core.data_manager import schema

async def setup(bot):
    trainer_table = bot.dbi.table('trainers')
    if await trainer_table.exists():
        return trainer_table
    columns = [schema.IDColumn('trainer_id', primary_key=True),
               schema.StringColumn('silph_id'),
               schema.IntColumn('pokebattler_id'),
               schema.Column('team', data_type=schema.IntegerSQL(small=True))]
    return await trainer_table.create(*columns)
