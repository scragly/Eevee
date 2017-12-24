import discord

class GuildDM:
    """Manage guild data/settings."""

    def __init__(self, db, guild):
        self._db = db
        if isinstance(guild, discord.Guild):
            guild = guild.id
        self.guild_id = int(guild)

    async def set_setting(self, key, value):
        query = '''INSERT INTO prefix (guild_id, prefix)
                   VALUES ($1,$2)
                   ON CONFLICT (guild_id) DO UPDATE SET
                   prefix = EXCLUDED.prefix'''
        results = await self._db.execute_transaction(
            query, self.guild_id, prefix)
        return results

    async def _reset_prefix(self):
        query = "DELETE FROM prefix WHERE guild_id = $1"
        results = await self._db.execute_transaction(query, self.guild_id)
        return results

    async def _set_prefix(self, prefix):
        query = '''INSERT INTO prefix (guild_id, prefix)
                   VALUES ($1,$2)
                   ON CONFLICT (guild_id) DO UPDATE SET
                   prefix = EXCLUDED.prefix'''
        results = await self._db.execute_transaction(
            query, self.guild_id, prefix)
        return results

    async def _get_prefix(self):
        query = "SELECT prefix FROM prefix WHERE guild_id=$1;"
        results = await self._db.execute_query(query, self.guild_id)
        return results[0] if results else None

    async def prefix(self, new_prefix: str = None):
        """Process guild prefix actions.

        Get current prefix by calling without args.
        Set new prefix by calling with the new prefix as an arg.
        Reset prefix to default by calling 'reset' as an arg.
        """
        if new_prefix:
            if new_prefix.lower() == "reset":
                return await self._reset_prefix()
            else:
                return await self._set_prefix(new_prefix)
        else:
            return await self._get_prefix()
