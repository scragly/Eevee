"""Public Tests Features Module"""

from .cog import PublicTests

def setup(bot):
    bot.add_cog(PublicTests(bot))
