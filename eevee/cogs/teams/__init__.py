from .teams import Teams

def setup(bot):
    bot.add_cog(Teams(bot))
