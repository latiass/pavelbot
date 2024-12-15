from abc import ABC
from dataclasses import dataclass
from typing import Dict


@dataclass
class NotifierUser(ABC):
    opts: Dict[str, any]
    short_name: str

@dataclass
class BskyNotifierUser(NotifierUser):
    pass


@dataclass
class DiscordNotifierUser(NotifierUser):
    channel: int


def parse_notifier_user_config(config: Dict[str, any], short_name: str) -> NotifierUser:
    match config['type']:
        case 'bluesky':
            return BskyNotifierUser(config, short_name)
        case 'discord':
            channel: int = config['channel']
            return DiscordNotifierUser(config, short_name, channel)
        case _:
            raise Exception(f'No configured notifier for type {config['name']}')
