import json
import discord
import requests
import datetime
import os

from discord.ext import tasks
from discord.abc import (GuildChannel, PrivateChannel)


class PicartoLiveNotif(discord.Client):
    headers = {
            'Accept': 'application/json',
            'X-CSRF-TOKEN': '',
            'User-Agent' : 'Mozilla/5.0 Firefox/130.0' # Need to fake this lol
        }

    class Stream:
        def __init__(self, username: str, options: dict):
            self.username = username
            # Fill in our options
            self.options = {
                'shortname' : options.get('shortname', username),
                'suppress_embed' : options.get('suppress_embed', False),
                'image' : options.get('image', None)
            }
            self.online = False
            self.posted = False

            # Check if the image exists
            if self.options['image'] and not os.path.isfile(self.options['image']):
                print(f"{self.timestamp()}: \"{self.options['image']}\" does not exist; defaulting to no image.")
                self.options['image'] = None

        # Get timestamp for logging
        def timestamp(self):
            timestamp = datetime.datetime.now().timestamp()
            return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

        async def update(self, channel: GuildChannel | PrivateChannel):
            response = requests.get('https://api.picarto.tv/api/v1/channel/name/' + self.username,
                headers = PicartoLiveNotif.headers, timeout = 10)
            rjson = response.json()
            self.online = rjson['online']

            # If online, post the message based on options chosen
            if self.online and not self.posted:
                if self.options['image']: # Image included, so post it
                    await channel.send(self.options['shortname'] + " is now live at https://picarto.tv/" + self.username,
                        file=discord.File(self.options['image']), suppress_embeds=self.options['suppress_embed'])
                else:
                    await channel.send(self.options['shortname'] + " is now live at https://picarto.tv/" + self.username,
                        suppress_embeds=self.options['suppress_embed'])
                self.posted = True
                print(f"{self.timestamp()}: {self.username} is now online.") # Logging
            elif not self.online and self.posted:
                self.posted = False
                print(f"{self.timestamp()}: {self.username} is now offline.")  # Logging

    def __init__(self, streams: dict, channel: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Which streams we check and info about them
        self.streams = [self.Stream(username, streams[username]) for username in streams.keys()]
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
            await stream.update(channel)

    @stream_alert.before_loop
    async def before_login(self):
        await self.wait_until_ready()  # wait until the bot logs in

# Grab our json config
try:
    with open('data.json', 'r', encoding='utf8') as file:
        data = json.load(file)
except FileNotFoundError:
    print("data.json not found, terminating.")
    exit(1)

# Initialize the bot and login
client = PicartoLiveNotif(streams = data['streams'], channel = data['channel'], intents=discord.Intents.default())
client.run(data['token'])
