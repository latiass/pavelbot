import asyncio
import json
import logging
from typing import Dict, List, Tuple

from notifier.notifier_adapter import NotifierAdapter, create_adapter as create_notifier_adapter, start_discord_bot
from notifier.notifier_user import parse_notifier_user_config
from stream.stream_adapter import PollingStreamAdapter, create_adapter as create_stream_adapter
from stream.stream_user import parse_stream_user_config
from user import User


_log = logging.getLogger(__name__)

class LiveNotifier:
    discord_token: str
    config: List[Tuple[User, List[PollingStreamAdapter], List[NotifierAdapter]]] = []

    def __init__(self, config_file_path: str):
        try:
            with open(config_file_path, 'r', encoding='utf8') as config_file:
                # TODO: type this better
                config_json: Dict[str, any] = json.load(config_file)
        except FileNotFoundError:
            raise Exception(msg = f'{config_file_path} not found.')
        
        self.discord_token = config_json['discord_token']
        
        # parse the users from the configuration
        users = self._parse_users(config_json['users'])

        # Create stream adapters for each user and wait for them to be ready
        self.config = self._generate_adapters(users)

        _log.info(f'Completed setting up LiveNotifier')
    
    async def start(self):
        # Initialize the discord bot
        start_task = start_discord_bot(self.discord_token)

        # Start the loop
        loop_task = self._update_loop()

        await asyncio.gather(start_task, loop_task)
    
    @staticmethod
    def _parse_users(config_json: List[Dict[str, any]]) -> List[User]:
        users: List[User] = []
        for config in config_json:
            short_name = config['short_name']

            streams = [parse_stream_user_config(stream_config) for stream_config in config['streams']]
            notifiers = [parse_notifier_user_config(notifier_config, short_name) for notifier_config in config['notifiers']]

            users.append(
                User(
                    short_name = short_name,
                    streams = streams,
                    notifiers = notifiers,
                )
            )
        return users
    
    @staticmethod
    def _generate_adapters(users: List[User]) -> List[Tuple[User, List[PollingStreamAdapter], List[NotifierAdapter]]]:
        config: List[Tuple[User, List[PollingStreamAdapter], List[NotifierAdapter]]] = []
        for user in users:
            stream_adapters = [create_stream_adapter(stream) for stream in user.streams]
            notifier_adapters = [create_notifier_adapter(notifier) for notifier in user.notifiers]
            config.append(tuple([user, stream_adapters, notifier_adapters]))
        return config
    
    async def _update_loop(self):
        while True:
            notify_tasks: List[asyncio.Task] = []
            
            _log.info(f'Checking for stream updates for {len(self.config)} users')
            for _, streams, notifiers in self.config:
                for stream in streams:
                    stream_update = stream.poll_stream()
                    if stream_update is not None:
                        for notifier in notifiers:
                            notify_tasks.append(notifier.notify(stream_update))
            await asyncio.gather(*notify_tasks)
            await asyncio.sleep(180)

# Initialize the bot and login
notifier = LiveNotifier(config_file_path='config.json')
asyncio.run(notifier.start())
