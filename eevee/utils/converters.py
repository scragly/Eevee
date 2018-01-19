from discord.ext import commands

class BotCommand(commands.Converter):
    async def convert(self, ctx, arg):
        cmd = ctx.bot.get_command(arg)
        if cmd is None:
            names = map(str, _unique(ctx.bot.walk_commands()))
            closest = difflib.get_close_matches(arg, names, cutoff=0.5)
            joined = 'Did you mean:\n' + '\n'.join(closest) if closest else ''
            raise commands.BadArgument(f"Command {arg} not found. {joined}")
        return cmd

class Multi(commands.Converter):
    def __init__(self, *types):
        self.types = types

    async def convert(self, ctx, arg):
        for type_ in self.types:
            try:
                return await ctx.command.do_conversion(ctx, type_, arg)
            except Exception as e:
                continue
        type_names = ', '.join([t.__name__ for t in self.types])
        raise commands.BadArgument(
            f"{arg} was not able to convert to the following types: "
            "{type_names}")

class Guild(commands.Converter):
    async def convert(self, ctx, arg):
        guild = None
        if arg.isdigit():
            guild = ctx.bot.get_guild(int(arg))
        if not guild:
            guild = ctx.bot.find_guild(arg)
        return guild