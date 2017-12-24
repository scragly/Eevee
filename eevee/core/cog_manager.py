import os
import pkgutil

from eevee.core import checks
from eevee import utils, command, group


class CogManager:
    """Commands to add, remove and change cogs for Eevee."""

    def __local_check(self, ctx):
        return checks.check_is_co_owner(ctx)

    @group(category="Owner")
    async def cog(self, ctx):
        """Commands to manage cogs."""
        if ctx.invoked_subcommand is None:
            await ctx.bot.send_cmd_help(ctx)

    @cog.command()
    async def list(self, ctx):
        """List all available cogs and their loaded status."""
        cog_folder = "cogs"
        cogs_dir = os.path.join(os.path.dirname(__file__), "..", cog_folder)
        cog_files = [name for _, name, _ in pkgutil.iter_modules([cogs_dir])]
        loaded_ext = []
        count_loaded = 0
        count_ext = 0
        msg = ""
        for ext in ctx.bot.extensions:
            loaded_ext.append(ext)
        for ext in cog_files:
            count_ext += 1
            ext_name = ("eevee.cogs."+ext)
            is_loaded = ext_name in loaded_ext
            status = ":black_small_square:"
            if is_loaded:
                count_loaded += 1
                status = ":white_small_square:"
            msg += "{0} {1}\n".format(status, ext)
        count_msg = "{} of {} cogs loaded.\n\n".format(
            count_loaded, count_ext)
        embed = utils.make_embed(msg_type='info',
                                 title='Available Cogs',
                                 content=count_msg+msg)
        await ctx.send(embed=embed)

    @cog.command()
    async def unload(self, ctx, cog):
        """Unload a cog."""
        bot = ctx.bot
        ext_name = ("eevee.cogs."+cog)
        if ext_name in bot.extensions:
            bot.unload_extension(ext_name)
            embed = utils.make_embed(msg_type='success',
                                     title=cog+' module unloaded.')
            await ctx.send(embed=embed)
        else:
            embed = utils.make_embed(
                msg_type='error', title=cog+' module not loaded.')
            await ctx.send(embed=embed)

    @cog.command()
    async def load(self, ctx, cog):
        """Load or reload a cog."""
        bot = ctx.bot
        cog_folder = "cogs"
        cogs_dir = os.path.join(os.path.dirname(__file__), "..", cog_folder)
        cog_files = [name for _, name, _ in pkgutil.iter_modules([cogs_dir])]
        if cog in cog_files:
            ext_name = ("eevee.cogs."+cog)
            was_loaded = ext_name in bot.extensions
            try:
                bot.unload_extension(ext_name)
                bot.load_extension(ext_name)
                if was_loaded:
                    msg = cog+' module reloaded.'
                else:
                    msg = cog+' module loaded.'
                embed = utils.make_embed(msg_type='success', title=msg)
                await ctx.send(embed=embed)
            except Exception as e:
                # logger.critical('Error loading cog: {} - {}: {}'.format(
                #    str(cog), type(e).__name__, e))
                embed = utils.make_embed(
                    msg_type='error',
                    title='Error when loading '+str(cog),
                    content='{}: {}'.format(type(e).__name__, e))
                await ctx.send(embed=embed)
                raise

        else:
            embed = utils.make_embed(
                msg_type='error',
                title=cog+' module not found.')
            await ctx.send(embed=embed)

    @cog.command()
    async def showext(self, ctx):
        bot = ctx.bot
        embed = utils.make_embed(msg_type='info',
                                 title='Raw Extension List',
                                 content='\n'.join(bot.extensions))
        await ctx.send(embed=embed)

    @command(category="Owner")
    async def reload_core(self, ctx):
        """Reload Core Commands."""
        bot = ctx.bot
        try:
            bot.unload_extension('eevee.core.commands')
            bot.load_extension('eevee.core.commands')
            embed = utils.make_embed(msg_type='success',
                                     title='Core Commands reloaded.')
            await ctx.send(embed=embed)
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            embed = utils.make_embed(msg_type='error',
                                     title='Error loading Core Commands',
                                     content=msg)
            await ctx.send(embed=embed)

    @command(category="Owner")
    async def reload_dm(self, ctx):
        """Reload Data Manager."""
        bot = ctx.bot
        try:
            bot.unload_extension('eevee.data_manager')
            bot.load_extension('eevee.data_manager')
            embed = utils.make_embed(msg_type='success',
                                     title='Data Manager reloaded.')
            await ctx.send(embed=embed)
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            embed = utils.make_embed(msg_type='error',
                                     title='Error loading Data Manager',
                                     content=msg)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(CogManager())
