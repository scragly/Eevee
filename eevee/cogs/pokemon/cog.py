import asyncio
import json
import os
import sqlite3

from eevee import group
from eevee.utils import make_embed, url_color
from eevee.utils.converters import Multi
from eevee.utils.formatters import code

from .objects import Pokemon

def init_pokedata(bot):
    with open(os.path.join(bot.data_dir, "raid_info.json")) as fp:
        bot.raid_info_json = json.load(fp)
        bot.raid_pokemon = bot.raid_info_json["raid_pkmn"]
        bot.raid_eggs = bot.raid_info_json["raid_eggs"]
    with open(os.path.join(bot.data_dir, "pkmn_info.json")) as fp:
        bot.pkmn_info_json = json.load(fp)
        bot.pkmn_info = bot.pkmn_info_json["pokemon"]
        bot.type_chart = bot.pkmn_info_json["type_chart"]


class Pokedex:
    """Pokemon Information and Management"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.config.command_categories["Pokedex"] = {
            "index" : "30",
            "description" : "Pokemon Information and Management"
        }
        self.type_emoji = bot.config.type_emoji
        init_pokedata(bot)

    def get_type_emoji(self, type):
        return self.type_emoji[type.lower()]

    def get_flavor(self, id):
        conn = sqlite3.connect('F:/Github/veekun-pokedex.sqlite/veekun-pokedex.sqlite')
        c = conn.cursor()
        c.execute('SELECT species_id, flavor_text '
                  'FROM pokemon_species_flavor_text '
                  'WHERE version_id = 26 AND language_id = 9 '
                  'AND species_id = {}'.format(id))
        return c.fetchone()[1]

    def pd_raid_info(self, pokemon):
        msg = (
            f'`Level                  :` {pokemon.raid_level}\n'
            f'`Max Capture CP         :` {pokemon.max_raid_cp()}\n'
            f'`Max CP w/ Weather Boost:` '
            f'{pokemon.max_raid_cp(weather_boost=True)}\n')
        return msg

    def pd_type_info(self, pokemon):
        type_effects = pokemon.type_effects_grouped
        ue_emoji = ' '.join(
            self.get_type_emoji(t) for t in type_effects['ultra'])
        se_emoji = ' '.join(
            self.get_type_emoji(t) for t in type_effects['super'])
        le_emoji = ' '.join(
            self.get_type_emoji(t) for t in type_effects['low'])
        we_emoji = ' '.join(
            self.get_type_emoji(t) for t in type_effects['worst'])

        msg = ""
        if ue_emoji:
            msg += f'`Ultra Effective:` {ue_emoji}\n'
        if se_emoji:
            msg += f'`Super Effective:` {se_emoji}\n'
        if le_emoji:
            msg += f'`Low Effect     :` {le_emoji}\n'
        if we_emoji:
            msg += f'`Worst Effect   :` {we_emoji}\n'

        return msg

    async def pd_pokemon(self, pokemon, only_type=False, only_raid=False):
        pkmn_no = str(pokemon.id).zfill(3)
        pkmn_url = ('https://raw.githubusercontent.com/FoglyOgly/'
                    f'Meowth/master/images/pkmn/{pkmn_no}_.png')
        pkmn_colour = await url_color(pkmn_url)
        embed = make_embed(
            icon='https://cdn.discordapp.com/emojis/351758295142498325.png',
            image=pkmn_url,
            msg_colour=pkmn_colour)

        types_str = ' '.join(self.get_type_emoji(t) for t in pokemon.types)

        if only_type:
            header = (f'{types_str}\n#{pkmn_no} - {pokemon.name.capitalize()}'
                      ' - Type Effectiveness')
            description = self.pd_type_info(pokemon)
        elif only_raid:
            header = (f'{types_str}\n#{pkmn_no} - {pokemon.name.capitalize()}'
                      ' - Raid Info')
            if pokemon.is_raid:
                description = self.pd_raid_info(pokemon)
            else:
                description = "This Pokemon does not currently appear in raids."
                
        else:
            header = f'{types_str}\n#{pkmn_no} - {pokemon.name.capitalize()}'
            description = code(self.get_flavor(pokemon.id).replace('\n', ' '))

        embed.add_field(
            name=header,
            value=description,
            inline=False)

        if only_type or only_raid:
            return embed

        embed.add_field(name='TYPE EFFECTIVENESS',
                        value=self.pd_type_info(pokemon),
                        inline=False)

        if pokemon.is_raid:
            embed.add_field(name='RAID INFO',
                            value=self.pd_raid_info(pokemon),
                            inline=False)

        return embed

    async def did_you_mean(self, ctx, pokemon):
        suggested = pokemon['suggested']
        original = pokemon['original']
        react_list = [
            '\N{WHITE HEAVY CHECK MARK}',
            '\N{NEGATIVE SQUARED CROSS MARK}'
        ]
        dym_msg = await ctx.send(f'Did you mean "{suggested}"?')
        def check(reaction, user):
            if reaction.message.id != dym_msg.id:
                return False
            if user.id != ctx.author.id:
                return False
            if reaction.emoji not in react_list:
                return False
            return True
        for r in react_list:
            await dym_msg.add_reaction(r)
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=30, check=check)
        except asyncio.TimeoutError:
            await dym_msg.clear_reactions()
            return

        await dym_msg.clear_reactions()
        if reaction.emoji == '\N{WHITE HEAVY CHECK MARK}':
            ctx.message.content = ctx.message.content.replace(
                original, suggested)
            await dym_msg.delete()
            await ctx.bot.process_commands(ctx.message)

    @group(category="Pokedex", aliases=["pd"], invoke_without_command=True)
    async def pokedex(self, ctx, *, pokemon: Pokemon):
        """Return Pokemon Info"""
        if isinstance(pokemon, Pokemon):
            embed = await self.pd_pokemon(pokemon)
            await ctx.send(embed=embed)
        else:
            await self.did_you_mean(ctx, pokemon)

    @pokedex.command()
    async def raid(self, ctx, *, arg: Multi(int, Pokemon)):
        """Return Raid Info"""
        if isinstance(arg, int):
            raid_level = arg
            raid_egg_url = ctx.bot.raid_eggs[f'{raid_level}']['img_url']
            raid_egg_colour = await url_color(raid_egg_url)
            pkmn_list = []
            for k, v in ctx.bot.raid_pokemon.items():
                level = v['level']
                if level == raid_level:
                    pkmn_list.append(k)
            embed = make_embed(
                msg_type='info',
                title=f'Level {raid_level} Raid List',
                msg_colour=raid_egg_colour, content=', '.join(pkmn_list))
            await ctx.send(embed=embed)

        elif isinstance(arg, Pokemon):
            embed = await self.pd_pokemon(arg, only_raid=True)
            await ctx.send(embed=embed)

        elif isinstance(arg, str):
            await self.did_you_mean(ctx, arg)
