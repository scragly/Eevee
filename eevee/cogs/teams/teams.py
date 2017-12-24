import discord
from discord.ext import commands

class Teams:
    """Team Management"""

    def __init__(self, bot):
        self.bot = bot

    def team_list(self):
        """Returns a list of playable teams"""
        config = self.bot.config
        teams = config['teams']['team_list']
        return teams

    @staticmethod
    def role_heirarchy_check(ctx: commands.Context, role: discord.Role):
        """Checks if the bot has a higher role than the given one."""
        return ctx.guild.me.top_role > role

    def get_team_role(self, guild: discord.Guild, team: str):
        """Returns the guild role for a given team."""
        return discord.utils.get(guild.roles, name=team)

    def get_team_roles(self, guild: discord.Guild):
        """Returns a list of guild roles for all teams."""
        teams = self.team_list()
        team_roles = []
        for team in teams:
            team_role = self.get_team_role(guild, team)
            if team_role:
                team_roles.append(team_role)
        return team_roles

    def get_team_colour(self, team: str):
        """Returns the teams colour as discord.Colour."""
        colour_dict = self.bot.config['teams']['team_colours']
        return discord.Colour(colour_dict[team])

    def get_team_emoji(self, team: discord.Role):
        """Returns the emoji representing the given team."""
        emoji_dict = self.bot.config['teams']['team_emoji']
        return emoji_dict[team.name]

    async def create_team_roles(self, guild: discord.Guild):
        """Creates new team roles for the guild.

        By default, each team role is assigned their default colours as
        set in the config file, and are set to be shown seperately in
        the member list.
        """
        teams = self.team_list()
        for team in teams:
            team_role = self.get_team_role(guild, team)
            if team_role is None:
                team_colour = self.get_team_colour(team)
                await guild.create_role(
                    reason="Eevee Bot auto-created team roles.",
                    name=team, colour=team_colour, hoist=True)

    @commands.command()
    async def team(self, ctx, team: str):
        """Set your team role."""
        guild = ctx.guild
        member = ctx.author
        team_roles = self.get_team_roles(guild)
        team_role = None

        if not team_roles:
            await ctx.send(_("Teams aren't setup for this server!"))
            return

        for role in team_roles:
            if role.name.lower() == team.lower():
                team_role = role
            if role in member.roles:
                await ctx.send(_("You already have a team role!"))
                return

        if team_role is None:
            msg = _("I don't know of any team named **{}**!\n"
                    "Try one of the following:").format(team)
            for role in team_roles:
                msg += "\n**{}**".format(role.name)
            await ctx.send(msg)
            return

        if not self.role_heirarchy_check(ctx, team_role):
            await ctx.send(_("There's an issue with this team role!\n"
                             "Please get an admin to check that the team "
                             "roles are below my highest role."))

        try:
            await member.add_roles(team_role)
            team_emoji = self.get_team_emoji(team_role)
            await ctx.send(_(
                "Welcome to {team_name}, {member}! {team_emoji}"
                "").format(team_name=team_role.name.capitalize(),
                           member=member.mention,
                           team_emoji=team_emoji))
        except discord.Forbidden:
            await ctx.send(_("I can't add roles!\n"
                             "Please get an admin to check my permissions."))
