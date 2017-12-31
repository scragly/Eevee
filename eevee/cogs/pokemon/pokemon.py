import json
import os

import discord
from discord.ext import commands

from eevee import group
from eevee.utils import make_embed, fuzzymatch, url_color

class Pokemon():
    """Represents a Pokemon"""

    def __init__(self, bot, pkmn, guild = None):
        self.bot = bot
        self.guild = guild
        self.name = pkmn
        self.id = list(bot.pkmn_info.keys()).index(pkmn)+1
        self.types = self.get_type(self.name)

    def __str__(self):
        return self.name

    @property
    def is_raid(self):
        """bool : Indicates if the pokemon can show in Raids"""
        return self.name in list(self.bot.raid_pokemon.keys())

    @property
    def raid_level(self):
        """Returns raid egg level"""
        return self.bot.raid_pokemon[self.name]["level"] if self.is_raid else None

    def max_raid_cp(self, weather_boost=False):
        """Returns max CP on capture after raid"""
        key = "max_cp_w" if weather_boost else "max_cp"
        return self.bot.raid_pokemon[self.name][key] if self.is_raid else None

    @property
    def role(self, guild=None):
        guild = guild if guild else self.guild
        return discord.utils.get(guild.roles, name=self.name)

    @property
    def weak_against(self):
        types_eff = {}
        for t, v in self.type_effects.items():
            if round(v, 3) > 1:
                types_eff[t] = v
        return types_eff

    @property
    def strong_against(self):
        types_eff = {}
        for t, v in self.type_effects.items():
            if round(v, 3) < 1:
                types_eff[t] = v
        return types_eff

    def get_type(self, pkmn):
        return self.bot.pkmn_info[pkmn]["types"]

    @property
    def type_effects(self):
        type_eff = {}
        for _type in self.types:
            for atk_type in self.bot.type_chart[_type]:
                if atk_type not in type_eff:
                    type_eff[atk_type] = 1
                type_eff[atk_type] *= self.bot.type_chart[_type][atk_type]
        return type_eff


class PkmnConverter(commands.Converter):
    """Converts to a Pokemon object"""

    async def convert(self, ctx, argument):
        pkmn_list = list(ctx.bot.pkmn_info.keys())
        match, score = self.get_name(pkmn_list, argument)
        if match:
            if score >= 80:
                result = Pokemon(ctx.bot, str(match), ctx.guild)
            else:
                result = str(match)

        if result is None:
            raise commands.errors.BadArgument(
                'Pokemon "{}" not valid'.format(argument))

        return result

    def get_name(self, pkmn_list, pkmn):
        match, score = fuzzymatch.get_match(pkmn_list, pkmn)
        if not match:
            return None, None
        return match, score


def init_pokedata(bot):
    with open(os.path.join(bot.data_dir, "raid_info.json")) as fp:
        raid_info_json = json.load(fp)
        bot.raid_pokemon = raid_info_json["raid_pkmn"]
        bot.raid_eggs = raid_info_json["raid_eggs"]
    with open(os.path.join(bot.data_dir, "pkmn_info.json")) as fp:
        pkmn_info_json = json.load(fp)
        bot.pkmn_info = pkmn_info_json["pokemon"]
        bot.type_chart = pkmn_info_json["type_chart"]


class Pokedex:
    """Pokemon Information and Management"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.config.command_categories["Pokedex"] = {
            "index" : "6",
            "description" : "Pokemon Information and Management"
        }
        self.type_emoji = bot.config.type_emoji
        init_pokedata(bot)

    def get_type_emoji(self, type):
        return self.type_emoji[type.lower()]

    @group(category="Pokedex", aliases=["pd"])
    async def pokedex(self, ctx, pokemon: PkmnConverter):
        """Return pokemon info"""
        if isinstance(pokemon, Pokemon):
            pkmn_no = str(pokemon.id).zfill(3)
            pkmn_url = ('https://raw.githubusercontent.com/FoglyOgly/'
                       f'Meowth/master/images/pkmn/{pkmn_no}_.png')
            pkmn_colour = await url_color(pkmn_url)
            embed = make_embed(
                title=f'#{pkmn_no} - {pokemon.name.capitalize()}',
                thumbnail=pkmn_url,
                msg_colour=pkmn_colour)
            weak_emoji = []
            for k, v in pokemon.weak_against.items():
                weak_emoji.append(self.get_type_emoji(k))
            strong_emoji = []
            for k, v in pokemon.strong_against.items():
                strong_emoji.append(self.get_type_emoji(k))
            type_emoji = []
            for _type in pokemon.types:
                type_emoji.append(self.get_type_emoji(_type))
            
            embed.add_field(name='Types',
                            value=' '.join(type_emoji), inline=False)
            embed.add_field(name='Weak Against',
                            value=' '.join(weak_emoji), inline=False)
            embed.add_field(name='Strong Against',
                            value=' '.join(strong_emoji), inline=False)
            if pokemon.is_raid:
                embed.add_field(name='Raid Level',
                                value=pokemon.raid_level, inline=False)
                embed.add_field(name='Raid Capture Max CP',
                                value=pokemon.max_raid_cp(), inline=False)
                embed.add_field(name='Raid Capture Max CP w/ Weather',
                                value=pokemon.max_raid_cp(weather_boost=True),
                                inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'Did you mean "{pokemon}"?')

    # @pokedex.command()
    # async def raids(self, ctx, level=None):
        
