"""This cog contains google related features."""

from .google_cog import Google


def setup(bot):
    bot.add_cog(Google(bot))
