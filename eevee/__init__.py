#!/usr/bin/python3
"""A Pokemon Go Community Bot for Discord.

Eevee is a Discord bot written in Python 3.6.1 using version 1.0.0a of the discord.py library.
It assists with the organisation of local Pokemon Go Discord servers and their members."""

__version__ = "2.0.0a0"

__author__ = "scragly"
__credits__ = ["FoglyOgly"]
__maintainer__ = "scragly"
__status__ = "Development"

from eevee.core.bot import command, group
from eevee.core import checks, errors
