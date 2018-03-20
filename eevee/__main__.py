"""Eevee Bot Module.

By using this command instead of ``eevee``, the bot will bypass the launcher.

Command:
    ``eevee-bot``

Options:
    -d, --debug   Enable debug mode.
"""

import argparse
import asyncio
import sys

import discord

from eevee.core import bot
from eevee.utils import ExitCodes, logger

if discord.version_info.major < 1:
    print("You are not running discord.py v1.0.0a or above.\n\n"
          "Eevee v2 requires the new discord.py library to function "
          "correctly. Please install the correct version.")
    sys.exit(1)

def run_eevee(debug=False, launcher=None):
    description = "Eevee v2 - Alpha"
    eevee = bot.Eevee(description=description, launcher=launcher, debug=debug)
    eevee.logger = logger.init_logger(eevee.data_dir, debug)
    eevee.load_extension('eevee.core.error_handling')
    eevee.load_extension('eevee.core.commands')
    eevee.load_extension('eevee.core.cog_manager')
    for ext in eevee.preload_ext:
        ext_name = ("eevee.cogs."+ext)
        eevee.load_extension(ext_name)
    loop = asyncio.get_event_loop()
    if eevee.token is None or not eevee.default_prefix:
        eevee.logger.critical("Token and prefix must be set in order to login.")
        sys.exit(1)
    try:
        loop.run_until_complete(eevee.start(eevee.token))
    except discord.LoginFailure:
        eevee.logger.critical("Invalid token")
        loop.run_until_complete(eevee.logout())
        eevee.shutdown_mode = ExitCodes.SHUTDOWN
    except KeyboardInterrupt:
        eevee.logger.info("Keyboard interrupt detected. Quitting...")
        loop.run_until_complete(eevee.logout())
        eevee.shutdown_mode = ExitCodes.SHUTDOWN
    except Exception as exc:
        eevee.logger.critical("Fatal exception", exc_info=exc)
        loop.run_until_complete(eevee.logout())
    finally:
        code = eevee.shutdown_mode
        sys.exit(code.value)

def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Eevee - Pokemon Go Bot for Discord")
    parser.add_argument(
        "--debug", "-d", help="Enabled debug mode.", action="store_true")
    parser.add_argument(
        "--launcher", "-l", help=argparse.SUPPRESS, action="store_true")
    return parser.parse_args()



def main():
    args = parse_cli_args()
    run_eevee(debug=args.debug, launcher=args.launcher)

if __name__ == '__main__':
    main()
