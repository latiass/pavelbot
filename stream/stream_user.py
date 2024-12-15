from abc import ABC
from dataclasses import dataclass
from typing import Dict

class StreamUser(ABC):
    pass

@dataclass
class PicartoStreamUser(StreamUser):
    picarto_username: str


def parse_stream_user_config(config: Dict[str, any]) -> StreamUser:
    match config['type']:
        case 'picarto':
            return PicartoStreamUser(config['username'])
        case _:
            raise Exception(f'No stream type configured for {config['type']}')
