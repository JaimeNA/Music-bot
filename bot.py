import discord

import youtube_dl

import asyncio

from discord.ext import commands

# youtube_dl variables
ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # Bind to ipv4 since ipv6 addresses cause issues at certain times
}

ffmpeg_options = {"options": "-vn"}

# bot variables
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents = intents)

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if "entries" in data:
            # takes the first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # connect the bot to active channel, and ownload file using ytdl and plays it
    @bot.command()
    async def pone(ctx, *, url):
       
        # error handling in case nobody is connected
        try:
            channel = ctx.author.voice.channel
        except:
            await ctx.reply(f"Conectate a un canal, sino como queres que haga")
            return

        if ctx.voice_client is None:
            await channel.connect()
        
        async with ctx.typing():

            # error handling in case the url is nor supported
            try:
                player = await YTDLSource.from_url(url)
            except:
                await ctx.reply(f"No puedo poner eso :thinking:")
                return

            ctx.voice_client.play(player, after=lambda e: print(f"Player error: {e}") if e else None)

        await ctx.reply(f"Ahora suena: {player.title}")

    # stops and disconnects the bot from voice
    @bot.command()
    async def para(ctx):
        
        await ctx.voice_client.disconnect()

bot.run('Token')
