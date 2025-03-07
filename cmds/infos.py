import discord
from discord.ext import commands
from calculatefuncs import *
from mcstatus import JavaServer

class Informations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
    @commands.command(
        name = "about",
        help = "About the bot",
        aliases = ["info", "information", "botinfo"]
    )
    async def botinfo(self, message):
        embed = discord.Embed(
            title = "About the KCServers Bot",
            description = f"""
__KCServers bot__
The KCServers bot is made to provide easy access to KCMC information, such as the players on a server, as well as a player's KCash and stats.
Players using this bot can also start up servers with a small fee.

__Currencies:__
There are 5 currencies used by this bot. 2 of which are exclusive to the bot.
**Credits**: The main currency of the bot. It is used with bot games, as well as exchanging Credits to KCash.
**Unity**: A rarer currency, usually used to perform tasks that may influence others. A maximum of 200 Unity can be stored, and a minimum of -100 Unity can be obtained. For every 1 Unity in debt, the amount of Credits earned decreases by 1%. Also, every 1 Unity above 100 will give +0.1% Credit Earnings.
**Gems**: A premium currency, usually only obtained in events. It can be used to be exchange into Credits and Unity, or purchase special items in the shop.
**Gold**: A currency that is obtained through player mining (Using the `{prefix}players mine` command). It can be exchanged into Credits
**KCash**: The global currency of KCMC. It is used in every server that supports the *KMCExtract* technology.
""",
            color = 0xFF00FF
        )
    
        await message.send(embed=embed)

        
    @commands.command(
        help = f"Get all server statuses",
    )
    @commands.cooldown(1, 10, commands.BucketType.channel) 
    async def servers(self, message):
    
        embed = discord.Embed(title="Fetching servers",description=f"Please wait while the bot fetches servers...", color=0x00FF00)
        msg = await message.send(embed=embed)

        
        embed = discord.Embed(title="Active Servers",description=f"List of servers online:", color=0x00FF00)
        
        serversToPing = {
            "RLWorld": ["192.168.1.71:25250"],
            "LTS KCSMP": ["smp.kcservers.ca"],
            "KCSkyblock": ["192.168.1.71:25000"],
            "KevChall": ["192.168.1.71:38125"],
            "TestServ": ["192.168.1.64:50000"]
        }

        for s in serversToPing:
            for ip in serversToPing[s]:
                print(ip)
                try:
                    server = JavaServer.lookup(ip, timeout = 1)
                    ss = server.status()

                    if ss.players.sample is not None:
                        players = ', '.join(i.name for i in ss.players.sample)
                    else:
                        players = 'No players online'

                    embed.add_field(name=f"{s} (Online)", value=f"Players ({ss.players.online}/{ss.players.max}): {players}", inline=False)

                except Exception as e:
                    embed.add_field(name=f"{s} (Offline)", value=f"Unable to get data: {e}", inline=False)



        await msg.edit(embed=embed)
