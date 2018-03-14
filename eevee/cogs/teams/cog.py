import re

import discord
from discord.ext import commands

from eevee import command, checks
from eevee.utils import make_embed

def has_no_team():
    def check(ctx):
        team_roles = ctx.command.callback.__class__.get_team_roles(ctx.guild)
        print(team_roles)
        for role in team_roles:
            if role in ctx.author.member.roles:
                return False
        return True
    return commands.check(check)

class Teams:
    """Team Management"""

    def __init__(self, bot):
        self.bot = bot
        self.team_list = bot.config.team_list
        self.team_colours = bot.config.team_colours
        self.team_emoji = bot.config.team_emoji
        self.bot.config.command_categories["Trainer"] = {
            "index" : "25",
            "description" : "Trainer Commands"
        }

    @staticmethod
    def role_heirarchy_check(ctx: commands.Context, role: discord.Role):
        """Checks if the bot has a higher role than the given one."""
        return ctx.guild.me.top_role > role

    def get_team_role(self, guild: discord.Guild, team: str):
        """Returns the guild role for a given team."""
        return discord.utils.get(guild.roles, name=team)

    def get_team_roles(self, guild: discord.Guild):
        """Returns a list of guild roles for all teams."""
        team_roles = []
        for team in self.team_list:
            team_role = self.get_team_role(guild, team)
            if team_role:
                team_roles.append(team_role)
        return team_roles

    def get_team_colour(self, team: str):
        """Returns the teams colour as discord.Colour."""
        if team in self.team_list:
            return discord.Colour(int(self.team_colours[team], 16))
        else:
            return None

    def get_team_emoji(self, team: discord.Role):
        """Returns the emoji representing the given team."""
        return self.team_emoji[team.name]

    @command(category="Server Config")
    @checks.is_admin()
    async def create_teams(self, ctx):
        """Creates new team roles for the guild.

        By default, each team role is assigned their default colours as
        set in the config file, and are set to be shown seperately in
        the member list.
        """
        new_teams = []
        existing_teams = []
        guild = ctx.guild
        for team in self.team_list:
            team_role = self.get_team_role(guild, team)
            if team_role is None:
                team_colour = self.get_team_colour(team)
                await guild.create_role(
                    reason="Eevee Bot auto-created team roles.",
                    name=team, colour=team_colour, hoist=True)
        embed = make_embed(msg_type='success', title="Team roles created!")
        await ctx.send(embed=embed)

    @command(category="Trainer")
    @has_no_team()
    async def team(self, ctx, team: str):
        """Set your team role."""
        guild = ctx.guild
        member = ctx.author
        team_roles = self.get_team_roles(guild)
        team_role = None

        if not team_roles:
            await ctx.send("Teams aren't setup for this server!")
            return

        for role in team_roles:
            if role.name.lower() == team.lower():
                team_role = role
            if role in member.roles:
                await ctx.send("You already have a team role!")
                return

        if team_role is None:
            msg = ("I don't know of any team named **{}**!\n"
                   "Try one of the following:").format(team)
            for role in team_roles:
                msg += "\n**{}**".format(role.name)
            await ctx.send(msg)
            return

        if not self.role_heirarchy_check(ctx, team_role):
            await ctx.send("There's an issue with this team role!\n"
                           "Please get an admin to check that the team "
                           "roles are below my highest role.")

        try:
            await member.add_roles(team_role)
            team_emoji = self.get_team_emoji(team_role)
            emoji_id = re.search(r"<:\w+:([\d]+)>", team_emoji).group(1)
            emoji = discord.utils.get(guild.emojis, id=int(emoji_id))
            embed = make_embed(
                title=f"Welcome to {team_role.name.capitalize()}, "
                      f"{member.display_name}!",
                msg_colour=team_role.colour,
                icon=emoji.url)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I can't add roles!\n"
                           "Please get an admin to check my permissions.")
