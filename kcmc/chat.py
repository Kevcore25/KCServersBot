"""
A communication between Discord and Minecraft.

Requires a setup in a YAML file with a valid RCON Port/Password as well as the LOG file.

Essentially, it is a glorified KMCExtract-like function.
No mods required.
"""
from os import path
import discord
import yaml
from discord.ext import commands, tasks
from calculatefuncs import *
from mcrcon import MCRcon
import traceback

if not path.exists('chatcommunicator.yml'):
    with open('chatcommunicator.yml', 'x') as f:
        f.write('')

seeks = {}

def parse(text: str):
    return text.replace('\\','\\\\').replace('*', '\\*').replace('_','\\_').replace('~', '\\~').replace('#', '\#')

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
                
                if channelID not in seeks:
                    seeks[channelID] = 0

                with open(logFile, 'rb', buffering=0) as f:
                    # Seek to prevent unnecessary reading
                    f.seek(seeks[channelID])

                    # Load file
                    lastLogs = f.read()
                
                # Add seek for next time
                seeks[channelID] += len(lastLogs)

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

                with MCRcon('127.0.0.1', password, port, timeout=1) as rcon:
                    rcon.command(f'tellraw @a ' + json.dumps(
                        {"text": f"<{username}> {text}", "color": "gray"}
                    ))
            except:
                traceback.print_exc()