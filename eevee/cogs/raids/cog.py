import discord
from discord.ext import commands

from eevee import command, checks
from eevee.utils import make_embed
from eevee.cogs.pokemon import GetPkmn

class Raids:
    """Raids Management"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.config.command_categories["Raids"] = {
            "index" : "20",
            "description" : "Commands for Reporting and Participating in Raids"
        }

    @command(category="Pokemon Raid")
    async def raid(self, ctx, pokemon: GetPkmn):

    admin_role = discord.utils.get(ctx.message.server.roles, name='Admin Role')
    if admin_role in botuser.roles:
