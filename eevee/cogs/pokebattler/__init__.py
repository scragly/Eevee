from .cog import PokeBattler
from .objects import PBRaid, Weather

def setup(bot):
    bot.add_cog(PokeBattler(bot))
