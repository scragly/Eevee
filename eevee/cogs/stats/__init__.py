"""This is a statistics cog."""

from .cog import Statistics

def setup(bot):
    bot.add_cog(Statistics(bot))
