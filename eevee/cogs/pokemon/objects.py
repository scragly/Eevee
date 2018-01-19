from discord.ext import commands

from eevee.utils import fuzzymatch

class Pokemon():
    """Represents a Pokemon"""

    __slots__ = ('name', 'id', 'types', 'bot', 'guild')

    def __init__(self, bot, pkmn, guild=None):
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
    def is_exraid(self):
        """bool : Indicates if the pokemon can show in Raids"""
        if self.is_raid:
            return self.bot.raid_pokemon[self.name].get('exraid', False)
        return False

    @property
    def raid_level(self):
        """Returns raid egg level"""
        return self.bot.raid_pokemon[self.name]["level"] if self.is_raid else None

    def max_raid_cp(self, weather_boost=False):
        """Returns max CP on capture after raid"""
        key = "max_cp_w" if weather_boost else "max_cp"
        return self.bot.raid_pokemon[self.name][key] if self.is_raid else None

    def role(self, guild=None):
        guild = guild if guild else self.guild
        return self.bot.get(guild.roles, name=self.name)

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

    @property
    def type_effects_grouped(self):
        type_eff_dict = {
            'ultra' : [],
            'super' : [],
            'low'   : [],
            'worst' : []
        }
        for t, v in self.type_effects.items():
            if v > 1.9:
                type_eff_dict['ultra'].append(t)
            elif v > 1.3:
                type_eff_dict['super'].append(t)
            elif v < 0.6:
                type_eff_dict['worst'].append(t)
            else:
                type_eff_dict['low'].append(t)
        return type_eff_dict

    @classmethod
    async def convert(cls, ctx, argument):
        if argument.isdigit():
            try:
                match = list(ctx.bot.pkmn_info.keys())[int(argument)-1]
                score = 100
            except IndexError:
                raise commands.errors.BadArgument(
                    'Pokemon ID "{}" not valid'.format(argument))
        else:
            pkmn_list = list(ctx.bot.pkmn_info.keys())
            match, score = fuzzymatch.get_match(pkmn_list, argument)
        if match:
            if score >= 80:
                result = cls(ctx.bot, str(match), ctx.guild)
            else:
                result = {
                    'suggested' : str(match),
                    'original'   : argument
                }

        if not result:
            raise commands.errors.BadArgument(
                'Pokemon "{}" not valid'.format(argument))

        return result

class RaidEgg:

    @classmethod
    async def convert(cls, ctx, argument):
        return cls(argument)
