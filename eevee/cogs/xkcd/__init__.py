"""Public Tests Features Module"""

from .cog import XKCD

def setup(bot):
    bot.add_cog(XKCD(bot))
