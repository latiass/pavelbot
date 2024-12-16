from abc import ABC, abstractmethod
import io
import logging
from typing import Callable, Dict

import discord
from discord.abc import GuildChannel, PrivateChannel
from discord.ext import commands
from PIL import Image

from notifier.notifier_user import BskyNotifierUser, DiscordNotifierUser, NotifierUser
from stream.stream_adapter import StreamUpdate


_log = logging.getLogger(__name__)
_bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
    
@_bot.event
async def on_ready():
    _log.info(f'Discord notifier logged in as {_bot.user} (ID: {_bot.user.id})')

async def start_discord_bot(token: str) -> None:
    await _bot.start(token)

class NotifierAdapter(ABC):
    @abstractmethod
    async def notify(self, stream_update: StreamUpdate) -> None:
        pass

    @abstractmethod
    def prepare_notifier(self):
        pass

class BskyNotifierAdapter(NotifierAdapter):
    notifier_user: BskyNotifierUser

    def __init__(self, user: BskyNotifierUser):
        super().__init__()
        self.notifier_user = user

    async def notify(self, stream_update: StreamUpdate) -> None:
        # TODO: implement me
        pass

    def prepare_notifier(self):
        # Nothing to prepare for bsky
        pass

class DiscordNotifierAdapter(NotifierAdapter):
    notifier_user: DiscordNotifierUser

    def __init__(self, user: DiscordNotifierUser):
        super().__init__()
        self.notifier_user = user

    async def notify(self, stream_update: StreamUpdate) -> None:
        await _bot.wait_until_ready()
        channel: GuildChannel | PrivateChannel = _bot.get_channel(self.notifier_user.channel)
        if stream_update.online:
            await channel.send(
                f'{self.notifier_user.short_name} is now live at {stream_update.url}',
                file = discord.File(image_to_byte_array(stream_update.image)),
                suppress_embeds = self.notifier_user.opts['suppress_embed'],
            )
        elif self.notifier_user.opts['notify_offline']:
            await channel.send(
                f'{self.notifier_user.short_name} is no longer live',
                suppress_embeds = self.notifier_user.opts['suppress_embed'],
            )

    def prepare_notifier(self):
        self.run(self.notifier_user.token)


def create_adapter(user: NotifierUser) -> NotifierAdapter:
    match user.__class__.__name__:
        case BskyNotifierUser.__name__:
            return BskyNotifierAdapter(user)
        case DiscordNotifierUser.__name__:
            return DiscordNotifierAdapter(user)
        case _:
            raise Exception(f'No registered adapter for user type {user.__class__}')

def image_to_byte_array(image: Image) -> bytes:
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format=image.format)
    return imgByteArr.getvalue()
