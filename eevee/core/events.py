import datetime
import traceback
import platform

import pkg_resources

from discord.ext import commands

INTRO = ("==================================\n"
         "Eevee - Pokemon Go Bot for Discord\n"
         "==================================\n")

def init_events(bot, launcher=None):

    log = bot.logger

    @bot.event
    async def on_connect():
        if hasattr(bot, 'launch_time'):
            print("Reconnected.")

    @bot.event
    async def on_ready():
        if not hasattr(bot, 'launch_time'):
            bot.launch_time = datetime.datetime.utcnow()
        if not launcher:
            print(INTRO)
        print("We're on!\n")
        eevee_ver = pkg_resources.get_distribution("eevee").version
        print(f"Eevee Version: {eevee_ver}\n")
        if bot.debug:
            dpy_ver = pkg_resources.get_distribution("discord.py").version
            print(f"Python Version: {platform.python_version()}")
            print(f"Discord.py Version: {dpy_ver}")
            print(f"Platform: {platform.platform()}\n")
        guilds = len(bot.guilds)
        users = len(list(bot.get_all_members()))
        if guilds:
            print(f"Servers: {guilds}")
            print(f"Members: {users}")
        else:
            print("I'm not in any server yet, so be sure to invite me!")
        if bot.invite_url:
            print(f"\nInvite URL: {bot.invite_url}\n")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await bot.send_cmd_help(ctx)
        elif isinstance(error, commands.BadArgument):
            await bot.send_cmd_help(ctx)
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("That command is disabled.")
        elif isinstance(error, commands.CommandInvokeError):
            # Need to test if the following still works
            """
            no_dms = "Cannot send messages to this user"
            is_help_cmd = ctx.command.qualified_name == "help"
            is_forbidden = isinstance(error.original, discord.Forbidden)
            if is_help_cmd and is_forbidden and error.original.text == no_dms:
                msg = ("I couldn't send the help message to you in DM. Either"
                       " you blocked me or you disabled DMs in this server.")
                await ctx.send(msg)
                return
            """
            log.exception("Exception in command '{}'"
                          "".format(ctx.command.qualified_name),
                          exc_info=error.original)
            message = ("Error in command '{}'. Check your console or "
                       "logs for details."
                       "".format(ctx.command.qualified_name))
            exception_log = ("Exception in command '{}'\n"
                             "".format(ctx.command.qualified_name))
            exception_log += "".join(traceback.format_exception(
                type(error), error, error.__traceback__))
            bot._last_exception = exception_log
            await ctx.send(message)

        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.CheckFailure):
            pass
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("That command is not available in DMs.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("This command is on cooldown. "
                           "Try again in {:.2f}s"
                           "".format(error.retry_after))
        else:
            log.exception(type(error).__name__, exc_info=error)

    @bot.event
    async def on_message(message):
        bot.counter["messages_read"] += 1
        await bot.process_commands(message)

    @bot.event
    async def on_resumed():
        bot.counter["sessions_resumed"] += 1

    @bot.event
    async def on_command(command):
        bot.counter["processed_commands"] += 1
