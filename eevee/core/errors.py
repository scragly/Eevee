from discord.ext import commands
from asyncpg import PostgresError


class PokemonNotFound(commands.CommandError):
    """Exception raised when Pokemon given does not exist."""
    def __init__(self, pokemon, retry=True):
        self.pokemon = pokemon
        self.retry = retry

class MissingSubcommand(commands.CommandError):
    pass
