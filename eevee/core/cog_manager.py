import pkgutil

from eevee.core import checks
from eevee import utils, command, group

class CogManager:
    """Commands to add, remove and change cogs for Eevee."""

    def __init__(self, bot):
        self.bot = bot
        self.all_exts = [
            ext for _, ext, _
            in pkgutil.iter_modules([self.bot.ext_dir])
            ]

    def __local_check(self, ctx):
        return checks.check_is_co_owner(ctx)

    @group(category="Owner", aliases=['ext'])
    async def extension(self, ctx):
        """Commands to manage extensions."""
        if ctx.invoked_subcommand is None:
            await ctx.bot.send_cmd_help(ctx)

    @extension.command(name="list")
    async def _list(self, ctx):
        """List all available extension modules and their status."""
        loaded_ext = []
        count_loaded = 0
        count_ext = 0
        msg = ""
        for ext in ctx.bot.extensions:
            loaded_ext.append(ext)
        for ext in self.all_exts:
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
                                 title='Available Extensions',
                                 content=count_msg+msg)
        await ctx.send(embed=embed)

    @extension.command(name='cogs')
    async def cogs(self, ctx):
        """List all loaded cogs."""
        cog_msg = '\n'.join(str(c) for c in ctx.bot.cogs)
        embed = utils.make_embed(msg_type='info',
                                 title='Loaded Cogs',
                                 content=cog_msg)
        await ctx.send(embed=embed)

    @extension.command()
    async def unload(self, ctx, cog):
        """Unload an extension."""
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

    @extension.group(invoke_without_command=True)
    async def load(self, ctx, *cogs):
        """Load or reload an extension."""
        if not cogs:
            await ctx.bot.send_cmd_help(ctx)
        available_exts = self.all_exts
        for cog in cogs:
            if cog in available_exts:
                ext_name = ("eevee.cogs."+cog)
                was_loaded = ext_name in ctx.bot.extensions
                try:
                    ctx.bot.unload_extension(ext_name)
                    ctx.bot.load_extension(ext_name)
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

    @extension.command()
    async def full(self, ctx):
        embed = utils.make_embed(msg_type='info',
                                 title='Full Extension List',
                                 content='\n'.join(ctx.bot.extensions))
        await ctx.send(embed=embed)

    @load.command(name="core")
    async def _core(self, ctx):
        """Reload Core Commands."""
        embed = self.load_extension('Core Commands', 'eevee.core.commands')
        await ctx.send(embed=embed)

    @load.command(name="cm")
    async def _cm(self, ctx):
        """Reload Cog Manager."""
        embed = self.load_extension('Cog Manager', 'eevee.core.cog_manager')
        await ctx.send(embed=embed)

    def load_extension(self, name, path):
        """Loads extensions and returns an embed with the result."""
        try:
            self.bot.unload_extension(path)
            self.bot.load_extension(path)
            embed = utils.make_embed(
                msg_type='success', title=f'{name} reloaded.')
            return embed
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            embed = utils.make_embed(
                msg_type='error', title=f'Error loading {name}', content=msg)
            return embed

    @command(category='Owner', name='reload', aliases=['load'])
    async def _reload(self, ctx, *, cogs):
        """Reload Cog"""
        ctx.message.content = f"{ctx.prefix}ext load {cogs}"
        await ctx.bot.process_commands(ctx.message)

def setup(bot):
    bot.add_cog(CogManager(bot))
