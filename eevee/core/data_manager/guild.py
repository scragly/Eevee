import discord

class GuildDM:
    """Manage guild data/settings."""

    def __init__(self, dbi, guild):
        self.dbi = dbi
        if isinstance(guild, discord.Guild):
            guild = guild.id
        self.guild_id = int(guild)

    async def settings(self, key=None, value=None, *, delete=False):
        config_table = self.dbi.table('guild_config')
        if delete:
            if key:
                return await config_table.delete(
                    guild_id=self.guild_id, config_name=str(key))
            else:
                return None
        if key is not None:
            if value is not None:
                return await config_table.upsert(
                    (self.guild_id, str(key), str(value)))
            else:
                return await self.dbi.settings_stmt.fetchval(
                    self.guild_id, str(key))
        else:
            return await config_table.get(guild_id=self.guild_id)

    async def prefix(self, new_prefix: str = None):
        """Add, remove and change custom guild prefix.

        Get current prefix by calling without args.
        Set new prefix by calling with the new prefix as an arg.
        Reset prefix to default by calling 'reset' as an arg.
        """
        pfx_tbl = self.dbi.table('prefix')
        gid = self.guild_id
        if new_prefix:
            if new_prefix.lower() == "reset":
                return await pfx_tbl.delete(guild_id=gid)
            else:
                return await pfx_tbl.upsert((gid, new_prefix))
        else:
            return await pfx_tbl.get_value('prefix', guild_id=gid)
