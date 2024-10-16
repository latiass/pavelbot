from discord.ext import tasks
import discord, requests, json

class PicartoLiveNotif(discord.Client):
    def __init__(self, streams: dict, channel: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Which streams we check and info about them
        self.streams = {}
        for stream in streams:
            self.streams[stream] = {
                'online': False,
                'posted': False
            }
        # ID of the channel we post messages in
        self.channel = channel
        # Headers the picarto API recommended, also have to fake UA for now to get the data
        self.headers = {
            'Accept': 'application/json',
            'X-CSRF-TOKEN': '',
            'User-Agent' : 'Mozilla/5.0 Firefox/130.0'
        }

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.stream_alert.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    @tasks.loop(seconds=180)  # task runs every 3 minutes
    async def stream_alert(self):
        for stream_name in self.streams.keys():
            # Check if stream status is online and update status
            response = requests.get('https://api.picarto.tv/api/v1/channel/name/' + stream_name,
                                    headers = self.headers)
            json = response.json()
            self.streams[stream_name]['online'] = json['online']

            # If online, post the message
            if self.streams[stream_name]['online'] and not self.streams[stream_name]['posted']:
                channel = self.get_channel(self.channel)
                await channel.send(stream_name + " is now live!")
                self.streams[stream_name]['posted'] = True
            elif not self.streams[stream_name]['online']:
                self.streams[stream_name]['posted'] = False

            print(f"Online: {self.streams[stream_name]['online']}; posted: {self.streams[stream_name]['posted']}")

    @stream_alert.before_loop
    async def before_login(self):
        await self.wait_until_ready()  # wait until the bot logs in

# Grab our json config
with open('data.json', 'r') as file:
    data = json.load(file)

# Initialize the bot and login
client = PicartoLiveNotif(streams = data['streams'], channel = data['channel'], intents=discord.Intents.default())
client.run(data['token'])
