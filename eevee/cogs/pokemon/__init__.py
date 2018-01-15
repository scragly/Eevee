from .cog import Pokedex

def setup(bot):
    bot.add_cog(Pokedex(bot))
