from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
import logging
from PIL import Image
import requests
from typing import Dict, Optional

from stream.stream_user import PicartoStreamUser, StreamUser


_log = logging.getLogger(__name__)

@dataclass
class StreamUpdate:
    url: str
    image: Image
    online: bool

class PollingStreamAdapter(ABC):
    @abstractmethod
    def poll_stream(self) -> Optional[StreamUpdate]:
        pass

class PicartoStreamAdapter(PollingStreamAdapter):
    stream_user: PicartoStreamUser
    online: bool = False

    headers: Dict[str, str] = {
        'Accept': 'application/json',
        'X-CSRF-TOKEN': '',
        'User-Agent' : 'Mozilla/5.0 Firefox/130.0' # Need to fake this lol
    }

    def __init__(self, stream_user: PicartoStreamUser):
        super().__init__()
        self.stream_user: PicartoStreamUser = stream_user
    
    def poll_stream(self) -> Optional[StreamUpdate]:
        response = requests.get(
            url = f'https://api.picarto.tv/api/v1/channel/name/{self.stream_user.picarto_username}',
            headers = self.headers,
            timeout = 10,
        )
        rjson = response.json()
        online = rjson['online']
        imageurl = rjson['thumbnails']['web']

        if online != self.online:
            self.online = online

            response = requests.get(
                url = imageurl,
                headers = self.headers,
                timeout = 10,
            )
            img = Image.open(BytesIO(response.content))

            _log.info(f'Discovered {self.stream_user.picarto_username} is {'now live' if online else 'no longer live'} on Picarto')
            return StreamUpdate(
                url = f'https://picarto.tv/{self.stream_user.picarto_username}',
                image = img,
                online = online
            )
        else:
            None

def create_adapter(stream_user: StreamUser) -> PollingStreamAdapter:
    match stream_user.__class__.__name__:
        case PicartoStreamUser.__name__:
            return PicartoStreamAdapter(stream_user)
        case _:
            raise Exception(f'No registered adapter for user type {stream_user.__class__.__name__}.')
