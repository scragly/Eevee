import discord

from eevee import group, Cog

from .objects import Trainer

class Trainers(Cog):
    """Trainer Features"""

    async def set_trainer(self, member, **data):
        return await Trainer.put(self.bot, member, **data)

    async def get_trainer(self, member):
        return await Trainer.get(self.bot, member)

    @group(invoke_without_command=True)
    async def trainer(self, ctx, trainer: discord.Member):
        trainer = await self.get_trainer(trainer)
        await ctx.send(f'Trainer: {trainer}\n'
                       f'Trainer ID: {trainer.id}\n'
                       f'Team: {trainer.team}\n'
                       f'Silph ID: {trainer.silph_id}\n'
                       f'Pokebattler ID: {trainer.pokebattler_id}')

    @trainer.command(name="set")
    async def _set(self, ctx, trainer: discord.Member, silph_id: str = None,
                   pokebattler_id: int = None, team: str = None):

        data = dict(silph_id=silph_id,
                    pokebattler_id=pokebattler_id,
                    team=team)

        data = {k:v for k, v in data.items() if v}

        trainer = await self.set_trainer(trainer, **data)

        await ctx.send(f'Trainer: {trainer}\n'
                       f'Trainer ID: {trainer.id}\n'
                       f'Team: {trainer.team}\n'
                       f'Silph ID: {trainer.silph_id}\n'
                       f'Pokebattler ID: {trainer.pokebattler_id}')

    @trainer.command()
    async def remove(self, ctx, trainer: discord.Member):
        trainer = await self.get_trainer(trainer)
        await trainer.delete()
        await ctx.send(f"{trainer}'s trainer data deleted.")
