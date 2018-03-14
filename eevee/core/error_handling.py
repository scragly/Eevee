import traceback

from discord.ext import commands

from eevee import errors

class ErrorHandler:

    async def on_command_error(self, ctx, error):
        if isinstance(error, errors.PokemonNotFound):
            await ctx.send(error.pokemon + ' not found.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.bot.send_cmd_help(
                ctx, title='Missing Arguments', msg_type='error')
        elif isinstance(error, commands.BadArgument):
            await ctx.bot.send_cmd_help(
                ctx, title=f'Bad Argument - {error}', msg_type='error')
        elif isinstance(error, errors.MissingSubcommand):
            await ctx.bot.send_cmd_help(
                ctx, title=f'Missing Subcommand - {error}', msg_type='error')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("That command is disabled.")
        elif isinstance(error, commands.CommandInvokeError):
            ctx.bot.logger.exception(
                "Exception in command '{}'".format(ctx.command.qualified_name),
                exc_info=error.original)
            message = ("Error in command '{}'. Check your console or "
                       "logs for details."
                       "".format(ctx.command.qualified_name))
            exception_log = ("Exception in command '{}'\n"
                             "".format(ctx.command.qualified_name))
            exception_log += "".join(traceback.format_exception(
                type(error), error, error.__traceback__))
            ctx.bot._last_exception = exception_log
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
            ctx.bot.logger.exception(type(error).__name__, exc_info=error)

def setup(bot):
    bot.add_cog(ErrorHandler())
