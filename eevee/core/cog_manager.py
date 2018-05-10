import pkgutil

from eevee.core import checks
from eevee import command, group

class CogManager:
    """Commands to add, remove and change cogs for Eevee."""

    def __init__(self, bot):
        self.bot = bot

    def __local_check(self, ctx):
        return checks.check_is_co_owner(ctx)

    @property
    def available_exts(self):
        return [i[1] for i in pkgutil.iter_modules([self.bot.ext_dir])]

    async def load_extension(self, ctx, name, extension):
        ext_loc, ext = extension.rsplit('.', 1)
        if ext not in self.available_exts and ext_loc == "eevee.cogs":
            return await ctx.error(f'Extention {name} not found')
        was_loaded = extension in ctx.bot.extensions
        try:
            ctx.bot.unload_extension(extension)
            ctx.bot.load_extension(extension)
        except Exception as e:
            await ctx.error(
                f'Error when loading extension {name}',
                f'{type(e).__name__}: {e}',
                log_level='critical')
        else:
            await ctx.success(
                f"Extension {name} {'reloaded' if was_loaded else 'loaded'}")

    @group(category="Owner", aliases=['ext'], invoke_without_command=True)
    async def extension(self, ctx):
        """Commands to manage extensions."""
        await ctx.bot.send_cmd_help(ctx)

    @extension.group(name="list", invoke_without_command=True)
    async def _list(self, ctx):
        """List all available extension modules and their status."""
        all_exts = self.available_exts
        not_emoji = "\N{BLACK SMALL SQUARE}"
        is_emoji = "\N{WHITE SMALL SQUARE}"
        status_list = []
        for ext in all_exts:
            is_loaded = f"eevee.cogs.{ext}" in ctx.bot.extensions
            status = is_emoji if is_loaded else not_emoji
            status_list.append(f"{status} {ext}")
        status_list.insert(0, f"{len(ctx.bot.extensions)} of {len(all_exts)}")
        await ctx.info('Available Extensions', '\n'.join(status_list))

    @_list.command()
    async def full(self, ctx):
        await ctx.info('Full Extension List', '\n'.join(ctx.bot.extensions))

    @extension.command(name='cogs')
    async def cogs(self, ctx):
        """List all loaded cogs."""
        await ctx.info('Loaded Cogs', '\n'.join(ctx.bot.cogs))

    @extension.command()
    async def unload(self, ctx, extension):
        """Unload an extension."""
        ext_name = f"eevee.cogs.{extension}"
        if ext_name in ctx.bot.extensions:
            ctx.bot.unload_extension(ext_name)
            await ctx.success(f'Extension {extension} unloaded')
        else:
            await ctx.error(f"Extension {extension} isn't loaded")

    @extension.group(invoke_without_command=True)
    async def load(self, ctx, *extensions):
        """Load or reload an extension."""
        if not extensions:
            return await ctx.bot.send_cmd_help(ctx)
        if len(extensions) > 5:
            return await ctx.warning(
                'Please limit extensions for loading to 5 or less.')
        for ext in extensions:
            name = ext.replace('_', ' ').title()
            await self.load_extension(ctx, name, f"eevee.cogs.{ext}")

    @load.command(name="core")
    async def _core(self, ctx):
        """Reload Core Commands."""
        await self.load_extension(ctx, 'Core Commands', 'eevee.core.commands')

    @load.command(name="cm")
    async def _cm(self, ctx):
        """Reload Cog Manager."""
        await self.load_extension(ctx, 'Cog Manager', 'eevee.core.cog_manager')

    @command(category='Owner', name='reload', aliases=['load'])
    async def _reload(self, ctx, *, cogs):
        """Reload Cog"""
        ctx.message.content = f"{ctx.prefix}ext load {cogs}"
        await ctx.bot.process_commands(ctx.message)

def setup(bot):
    bot.add_cog(CogManager(bot))
