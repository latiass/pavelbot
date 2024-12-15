from dataclasses import dataclass
from typing import List
from notifier.notifier_user import NotifierUser
from stream.stream_user import StreamUser

@dataclass
class User:
    short_name: str
    streams: List[StreamUser]
    notifiers: List[NotifierUser]
