import asyncio
import importlib
import logging
import sys

class Cog:
    def __init__(self, bot):
        self.bot = bot
        self.cog_table = None
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
        self.cog_table = await module.setup(self.bot)
