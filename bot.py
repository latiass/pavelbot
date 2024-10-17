import json

import discord
import requests
from discord.ext import tasks
from discord.abc import (GuildChannel, Thread, PrivateChannel)


class PicartoLiveNotif(discord.Client):
    headers = {
            'Accept': 'application/json',
            'X-CSRF-TOKEN': '',
            'User-Agent' : 'Mozilla/5.0 Firefox/130.0'
        }

    class Stream:
        def __init__(self, username):
            self.username = username
            self.online = False
            self.posted = False
        async def update(self, channel: GuildChannel | Thread | PrivateChannel):
            print('hoo')
            response = requests.get('https://api.picarto.tv/api/v1/channel/name/' + self.username,
                headers = PicartoLiveNotif.headers, timeout = 10)
            rjson = response.json()
            self.online = rjson['online']

            # If online, post the message
            if self.online and not self.posted:
                await channel.send(self.username + " is now live!")
                self.posted = True
            elif not self.online:
                self.posted = False

            print(f"Online: {self.online}; posted: {self.posted}")


    def __init__(self, streams: dict, channel: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Which streams we check and info about them
        self.streams = [self.Stream(stream) for stream in streams]
        # ID of the channel we post messages in
        self.channel = channel

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.stream_alert.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    @tasks.loop(seconds=180)  # task runs every 3 minutes
    async def stream_alert(self):
        channel = self.get_channel(self.channel)
        for stream in self.streams:
            stream.update(channel)

    @stream_alert.before_loop
    async def before_login(self):
        await self.wait_until_ready()  # wait until the bot logs in


# Grab our json config
with open('data.json', 'r', encoding='utf8') as file:
    data = json.load(file)

# Initialize the bot and login
client = PicartoLiveNotif(streams = data['streams'], channel = data['channel'], intents=discord.Intents.default())
client.run(data['token'])
