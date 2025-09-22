"""
A communication between Discord and Minecraft.

Requires a setup in a YAML file with a valid RCON Port/Password as well as the LOG file.

Essentially, it is a glorified KMCExtract-like function.
No mods required.
"""

RCON_IP = '127.0.0.1'

from os import path
import discord
import yaml
from discord.ext import commands, tasks
from calculatefuncs import *
from mcrcon import MCRcon
import traceback
from PIL import Image

if not path.exists('chatcommunicator.yml'):
    with open('chatcommunicator.yml', 'x') as f:
        f.write('')

seekinfo = {}

def parse(text: str):
    return text.replace('\\','\\\\').replace('*', '\\*').replace('_','\\_').replace('~', '\\~').replace('#', '\\#')

class ChatCommunicator(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        with open('chatcommunicator.yml', 'r') as f:
            self.servers: dict[str, str] = yaml.safe_load(f)

        self.loop.start()
        self.started = True

    def getRCON(self, properties: list[str]):
        password = port = None

        for ln in properties:
            try:
                p, v = ln.split('=')
                match p:
                    case "rcon.port":
                        port = int(v)
                    case "rcon.password":
                        password = v.rstrip()
            except: pass           
        
        return password, port
    
    @tasks.loop(seconds = 0.2)
    async def loop(self):
        try:
            # Get servers
            with open('chatcommunicator.yml', 'r') as f:
                self.servers: dict[str, str] = yaml.safe_load(f)

            for channelID, server in self.servers.items():
                descriptions = []

                # Get the LOG file
                logFile = path.join(server['Folder'], 'logs', 'latest.log')
                
                # Register if not already
                if channelID not in seekinfo:
                    seekinfo[channelID] = [0, path.getmtime(logFile)]

                # Check if modified date is newer than the old one
                size = path.getsize(logFile)
                if size > seekinfo[channelID][1]:
                    seekinfo[channelID][1] = size
                elif size < seekinfo[channelID][1]:
                    # Set seek to 0 in case log is rewritten.
                    # Prevents an edge case
                    seekinfo[channelID] = [0, size]
                else:
                    # Otherwise, to conserve resources, do not run
                    continue

                with open(logFile, 'rb') as f:
                    # Seek to prevent unnecessary reading
                    f.seek(seekinfo[channelID][0])

                    # Load file
                    lastLogs = f.read()
                
                # Add seek for next time
                seekinfo[channelID][0] += len(lastLogs)

                lastLogs = lastLogs.decode()

                # Don't send on first time
                if self.started: 
                    lastLogs = ""
                    self.started = False

                # Iterate through the logs
                for ln in lastLogs.splitlines():
                    # Check for chat MSG
                    if '<' in ln and '>' in ln and 'INFO' in ln:
                        # Get player
                        player = ln.split('<', 1)[1].split('>')[0]
                        message = ln.split('<', 1)[1].split('> ', 1)[1]

                        descriptions.append(f'**{parse(player)}**: {parse(message)}')

                    elif 'lost connection' in ln or 'joined the game' in ln:
                        descriptions.append('**' + parse(ln.split(': ', 1)[1]) + '**')

                if len(descriptions) > 0:
                    channel = self.bot.get_channel(channelID)
                    await channel.send('\n'.join(descriptions))
        except:
            traceback.print_exc()

    @commands.Cog.listener("on_message")
    async def getmsg(self, message: discord.Message):
        channelID = message.channel.id

        if channelID in self.servers and message.author.id != self.bot.user.id:
            try:
                u = User(message.author.id)

                # Get username
                ign = u.getData('settings').get('ign', 'N/A')
                username = f"{message.author.display_name} ({ign})"

                # Get the properties of the file
                propertiesFile = path.join(self.servers[channelID]['Folder'], 'server.properties')
                with open(propertiesFile, 'r') as f:
                    password, port = self.getRCON(f.readlines())

                # Get text
                text = message.clean_content[:100]

                with MCRcon(RCON_IP, password, port, timeout=1) as rcon:
                    rcon.command(f'tellraw @a ' + json.dumps(
                        {"text": f"<{username}> {text}", "color": "gray"}
                    ))

                # Attachments?
                if len(message.attachments) > 0 and message.attachments[0].content_type.startswith('image'):
                    try:
                        await self.send_attachment(message, password, port)
                    except: 
                        traceback.print_exc()

                # Possible Bot phrases
                await self.bot_phrases(message,  password, port)    
            except:
                traceback.print_exc()

    async def bot_phrases(self, message: discord.Message,  password, port):
        # Get text
        text = message.clean_content[:100].lower().strip()

        # Show list of players
        if (
            ("anyone on" in text) or
            ('player list' in text) or
            text.startswith('/list') or
            ('who' in text and ' on' in text) or
            ('anyone here' in text) or 
            ('anyone around' in text) or
            ('anyone' in text and ' active' in text)
        ):
            with MCRcon(RCON_IP, password, port, timeout=1) as rcon:
                players = rcon.command('list')

            await message.channel.send(f'{message.author.mention}: {players}')

    async def send_attachment(self, message: discord.Message, password, port):
        # Get attachment (image) and save it
        p = path.join('temp', 'attachment')
        await message.attachments[0].save(p)

        img = Image.open(p)

        # 41 is the max for this algorithm to work with RCON
        output_width = 41

        # Resize image
        width, height = img.size
        aspect_ratio = height / width
        new_height = int(output_width * aspect_ratio * 0.55) 
        img = img.resize((output_width, new_height))

        # conver to grayscale for brightness
        gray_img = img.convert('L')

        char_set = " -=+#%@ "

        lines = []

        for y in range(new_height):
            result = []
            for x in range(output_width):
                pixel_color = img.getpixel((x, y))
                pixel_intensity = gray_img.getpixel((x, y))

                char_index = int((pixel_intensity / 255) * (len(char_set) - 1))
                char = char_set[char_index]

                r, g, b = pixel_color
                color_code = f"#{r:02X}{g:02X}{b:02X}"

                result.append({"text": char, "color": color_code})
                
            lines.append(json.dumps(result))

        with MCRcon(RCON_IP, password, port, timeout=1) as mcr:
            for line in lines:
                mcr.command("tellraw @a " + line)