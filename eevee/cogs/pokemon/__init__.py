from .cog import Pokedex
from .objects import Pokemon

def setup(bot):
    bot.add_cog(Pokedex(bot))
