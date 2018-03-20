from eevee import command
from eevee.cogs.pokemon import Pokemon
from .objects import Weather, PBRaid


class PokeBattler:
    """PokeBattler integration."""

    PBRaid = PBRaid

    def __init__(self, bot):
        self.bot = bot
        self.bot.config.command_categories["PokeBattler"] = {
            "index" : "40",
            "description" : "PokeBattler integration"
        }

    @command()
    async def counters(self, ctx, pkmn: Pokemon,
                       weather: Weather.match_name = Weather.DEFAULT,
                       move1=None, move2=None, userid=None):
        """Simulate a Raid battle with Pokebattler.

        Weather options:
          None/Extreme, Clear, Rainy,
          PartlyCloudy, Cloudy,
          Windy, Snow, Fog
        """
        if not pkmn.is_raid:
            msg = "This Pokemon does not appear in a raid."
            await ctx.embed(msg, msg_type='error')
            return

        async with ctx.typing():
            pb_raid = await PBRaid.get(self.bot, pkmn, weather=weather, userid=userid)

        if move1 and move2:
            pb_raid.set_moveset([move1, move2])

        title = (f'{pkmn.name.title()} - Raid Level {pkmn.raid_level}'
                 f' - {pb_raid.weather.name.title()}')
        pbtlr_icon = 'https://www.pokebattler.com/favicon-32x32.png'
        stats_msg = f"**CP:** {pb_raid.raid_cp}\n"
        if pb_raid.moveset:
            stats_msg += f"**Moveset:** {' | '.join(pb_raid.moveset)}\n"
        else:
            stats_msg += f"**Moveset:** Unknown\n"
        if pb_raid.userid:
            stats_msg += f"**Pokebox UserID:** {pb_raid.userid}"
        else:
            stats_msg += f"**Attacker Level:** {pb_raid.atk_lvl}"
        
        pkmn_colour = await pkmn.colour()
        embed = await ctx.embed(
            title, title_url=pb_raid.public_url,
            icon='https://i.imgur.com/fn9E5nb.png', thumbnail=pkmn.img_url,
            footer_icon=pbtlr_icon, footer='Results courtesy of Pokebattler',
            colour=pkmn_colour, send=False)
        embed.add_field(name='Raid Stats', value=stats_msg, inline=False)
        max_power = None
        for counter in pb_raid.counters:
            if not max_power:
                max_power = counter.rating
            power = int(counter.rating / max_power*100)
            moves = " | ".join(counter.moveset)
            name = f"{counter.name.title()} (#{counter.id})  {power}%"
            embed.add_field(name=name, value=f"CP {counter.cp}\n{moves}", inline=True)
        fast_moves = ', '.join(pb_raid.fast_moves)
        charge_moves = ', '.join(pb_raid.charge_moves)
        move_msg = (f"**Fast Moves:** {fast_moves}\n"
                    f"**Charge Moves:** {charge_moves}")
        embed.add_field(name='Available Moves', value=f"{move_msg}", inline=True)
        await ctx.send(embed=embed)
