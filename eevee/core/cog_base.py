import asyncio
import importlib
import logging
import sys

from eevee.utils import Map

class Cog:
    def __init__(self, bot):
        self.bot = bot
        self.tables = None
        module = self.__class__.__module__
        cog = self.__class__.__name__
        log_name = f"{module}.{cog}"
        self.logger = logging.getLogger(log_name)
        tbl_mod_name = f"{'.'.join(module.split('.')[:-1])}.tables"
        try:
            tbl_mod = importlib.import_module(tbl_mod_name, module)
        except ModuleNotFoundError:
            pass
        else:
            if not hasattr(tbl_mod, 'setup'):
                del tbl_mod
                del sys.modules[tbl_mod_name]
            else:
                asyncio.run_coroutine_threadsafe(
                    self._table_setup(tbl_mod), bot.loop)

    async def _table_setup(self, module):
        cog_name = self.__class__.__name__
        cog_tables = module.setup(self.bot)
        if not isinstance(cog_tables, (list, tuple)):
            cog_tables = [cog_tables]
        self.tables_tables = Map({t.name:t for t in cog_tables})
        for table in self.tables_tables.values():
            if await table.exists():
                self.logger.info(
                    f'Cog table {table.name} for {cog_name} found.')
                table.new_columns = []
                continue
            await table.create()
            self.logger.info(f'Cog table {table.name} for {cog_name} created.')
