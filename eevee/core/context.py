from discord.ext import commands

class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = None

    async def ask_confirmation(message, *, timeout=30.0, delete_after=True,
                               author_id=None, destination=None):
        """An interactive reaction confirmation dialog.

        Parameters
        -----------
        message: Union[str, discord.Embed]
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        reacquire: bool
            Whether to release the database connection and then acquire it
            again when we're done.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author of the
            Context's message.
        destination: Optional[discord.abc.Messageable]
            Where the prompt should be sent. Defaults to the channel of the
            Context's message.

        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``False`` if explicit deny,
            ``None`` if deny due to timeout
        """

        # We can also wait for a message confirmation as well. This is faster, but
        # it's risky if there are two prompts going at the same time.
        # TODO: Possibly support messages again?

        destination = destination or self.channel
        with contextlib.suppress(AttributeError):
            if not destination.permissions_for(self.me).add_reactions:
                raise RuntimeError('Bot does not have Add Reactions permission.')

        config = self.bot.emoji_config
        confirm_emoji, deny_emoji = emojis = [config.confirm, config.deny]
        is_valid_emoji = frozenset(map(str, emojis)).__contains__

        instructions = f'React with {confirm_emoji} to confirm or {deny_emoji} to deny\n'

        if isinstance(message, discord.Embed):
            message.add_field(name="Instructions", value=instructions, inline=False)
            msg = await destination.send(embed=message)
        else:
            message = f'{message}\n\n{instructions}'
            msg = await destination.send(message)

        author_id = author_id or self.author.id

        def check(emoji, message_id, channel_id, user_id):
            if message_id != msg.id or user_id != author_id:
                return False

            result = is_valid_emoji(str(emoji))
            print(emojis)
            print(result, 'emoji:', emoji)
            return result

        for em in emojis:
            # Standard unicode emojis are wrapped in _ProxyEmoji in core/bot.py
            # because we need a url property. This is an issue because
            # message.add_reaction will just happily pass the _ProxyEmoji raw,
            # causing a 400 Bad Request due to Discord not recognizing the object.
            #
            # This is the cleanest way to do it withour resorting to monkey-
            # patching the discord.Message.add_reaction method. Since we're using
            # the emojis defined in emojis.py, we only need to worry about two types:
            # _ProxyEmoji and discord.Emoji, so we can just do a simple isinstance
            # check for discord.Emoji so we don't need to import _ProxyEmoji.
            #
            # It also doesn't matter if the confirm/deny emojis are None. That's the
            # user's fault.
            if not isinstance(em, discord.Emoji):
                em = str(em)

            await msg.add_reaction(em)

        if reacquire:
            await self.release()

        try:
            emoji, *_, = await self.bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
            # Extra str cast for the case of _ProxyEmojis
            return str(emoji) == str(confirm_emoji)
        finally:
            if reacquire:
                await self.acquire()

            if delete_after:
                await msg.delete()