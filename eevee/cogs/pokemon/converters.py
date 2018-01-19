from discord.ext import commands

class PokedexEntry(commands.Converter):
    """Converts to a Raid Egg object"""

    async def convert(self, ctx, argument):
        return
