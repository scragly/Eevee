import logging

class UnknownEventLogging:
    def __init__(self, bot):
        self.bot = bot

    async def on_socket_response(self, msg):
        event = msg.get('t')
        if not event:
            return

        if hasattr(self.bot._connection, f'parse_{event.lower()}'):
            return

        log = logging.getLogger('discord')
        log.info(f'Unknown Discord Event {event}. Message: {msg}')
        print(f'Unknown Discord Event {event}')
