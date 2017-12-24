from .pokemon import Pokedex
from .pokemon import PkmnConverter

def setup(bot):
    bot.add_cog(Pokedex(bot))
