from discord.ext.commands import MemberConverter

class Trainer:
    """Represents a user of Meowth, with their relevant persistant info."""

    __slots__ = ('bot', 'member', '_data', 'table')

    def __init__(self, bot, member):
        self.bot = bot
        self.member = member
        self._data = {}
        self.table = bot.dbi.table('trainers').where(trainer_id=self.id)

    def __str__(self):
        return self.member.__str__()

    def __getattr__(self, name):
        return getattr(self.member, name, None)

    @property
    def silph_id(self):
        return self._data.get('silph_id', None)

    @property
    def pokebattler_id(self):
        return self._data.get('pokebattler_id', None)

    @property
    def team(self):
        return self._data.get('team', None)

    async def update_data(self, **data):
        if data:
            self._data = dict(self._data, **data)
        result = await self.table.upsert(**self._data)

    async def get_data(self):
        data = await self.table.get_first()
        self._data = data if data else {}

    async def delete(self):
        await self.table.delete()

    @classmethod
    async def convert(cls, ctx, argument):
        member = await MemberConverter.convert(ctx, argument)
        instance = cls(ctx.bot, member)
        await instance.get_data()
        return instance if member else None

    @classmethod
    async def get(cls, bot, member):
        instance = cls(bot, member)
        await instance.get_data()
        return instance

    @classmethod
    async def put(cls, bot, member, **data):
        instance = cls(bot, member)
        if data:
            await instance.update_data(**data)
        return instance
