from .cog import PokeBattler

def setup(bot):
    bot.add_cog(PokeBattler(bot))
