import discord
from discord.ext import commands
from calculatefuncs import *
from mcstatus import JavaServer
import dns.resolver
import threading
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
The intended use of the KCServers bot is made **to provide easy access to KCMC information**, such as the players on a server, as well as a player's KCash and stats.
The KCServers Bot also comes with a **unique economy system** that provides gambling and Minecraft-related games.

__Currencies:__
There are 5 currencies used by this bot. 2 of which are exclusive to the bot.
**Credits**: The main currency of the bot. It is used with bot games, as well as exchanging Credits to KCash.

**Unity**: A unit of status measurement (think of it as Reputation). A maximum of 200 Unity can be stored, and a minimum of -100 Unity can be obtained. 
For every 1 Unity in debt, the amount of Credits earned decreases by 1%. Also, every 1 Unity above 100 will give +0.1% Credit Earnings.
Overflowing Unity will be converted into Credits (Rate: 1 Unity > 1 Credit)

**Gems**: A premium currency, usually only obtained in events and seasonal resets.
It can be used for exchanging Gems into Credits and Unity, or purchasing special items in the shop.

**Gold**: A currency that is obtained through player mining (Using the `{prefix}players mine` command).
As of V.5.0, the players system has been **deprecated.** The players system may be rebuilt in the future.

**KCash**: The global currency of KCMC. It is used in every server that supports the *KMCExtract* technology.
If you are a new KCMC player, you may ask to claim a **free 10,000 KCash reward.**
-# Offer only available to new players after 2025.

""",
            color = 0xFF00FF
        )
    
        await message.send(embed=embed)

    @commands.command(
        name = "terms",
        help = "Useful definitions for dedicated users",
        aliases = ["definitions", "defs"]
    )
    async def terms(self, message):
        embed = discord.Embed(
            title = "",
            description = f"""
__Wealth Power (WP)__
Wealth power is an important feature of KCServers Bot that measures how rich you are.
It is calculated using: `Wealth / ((Total Wealth of all Members - Wealth) / Number of Users)`
-# Remember, wealth is simply `Credits + BS% * Bot's Credits`
When used in calculations, there are 3 main generations which affect WP:
* Gen 2: `Amount / (Wealth Power), Wealth Power > 1`
* Gen 3: Every 20% WP after 100% causes earnings to reduce by 1%, up to -50% earnings
* Gen 4: A 1/Gen 3, making higher WP giving more, up to 2x more


""",
            color = 0xFF00FF
        )
    
        await message.send(embed=embed)

        
    @commands.command(
        help = f"Get all server statuses",
        description = f"""You may specify optional arguments. The default argument is "quick multi".
quick - Retrieves data faster by lowering the timeout from 1s to 0.5s
long - Sets timeout to 3s
multi - Request servers in parallel. Without this, requests are done sequentially.
hide - Hides offline servers (unable to connect)
detail - Also shows the server's MOTD / description
"""
    )
    @commands.cooldown(1, 10, commands.BucketType.channel) 
    async def servers(self, message, *, args: str = "quick multi"):
    
        embed = discord.Embed(title="Fetching servers",description=f"Please wait while the bot fetches servers...", color=0x00FF00)
        msg = await message.send(embed=embed)

        args = args.split(' ')

        embed = discord.Embed(title="Active Servers",description=f"List of servers online:", color=0x00FF00)

        kcmcnames = dns.resolver.resolve("kcmcnames.kcservers.ca", "TXT")[0].to_text()[1:-1]
        servers = kcmcnames.split(";")

        used = []

        if "quick" in args:
            timeout = 0.5
        elif "long" in args:
            timeout = 3
        else:
            timeout = 1

        def getServ(server: str, v: str):
            try:
                server = JavaServer.lookup(ip, timeout = timeout)
                ss = server.status()

                if ss.players.sample is not None:
                    players = ', '.join(i.name for i in ss.players.sample)
                else:
                    players = 'No players online'

                if "detail" in args or "detailed" in args:
                    motd = ss.motd.to_ansi().replace("\x1b","")
                    embed.add_field(name=f"{v} (Online)", value=f"```ansi\n{motd}```\nPlayers ({ss.players.online}/{ss.players.max}):\n-# {players}", inline=False)
                else:
                    embed.add_field(name=f"{v} (Online)", value=f"Players ({ss.players.online}/{ss.players.max}): {players}", inline=False)

            except Exception as e:
                if "hide" not in args:
                    embed.add_field(name=f"{v} (Offline)", value=f"Unable to get data: {e}", inline=False)

        for server in servers:
            try:
                k, v = server.split(":")
            except ValueError:
                continue

            if v in used:
                continue

            used.append(v)

            ip = k + ".kcservers.ca"

            if "multi" in args:
                threading.Thread(target=getServ, args=(ip, v)).start()
                time.sleep(0.05)
            else:
                getServ(ip, v)

        if "multi" in args: time.sleep(timeout)



        await msg.edit(embed=embed)



    @commands.command(
        help = f"Guides on how to earn a currency.\nFormat: {prefix}earn <credits | unity | gems>",
        aliases = ['howtoearn', 'waystoearn'],
    )
    async def earn(self, message, currency: str): 
        currency = currency.lower()
        
        if currency in WAYS_TO_EARN:
            await message.send(embed=basicMsg(f"Ways to earn {currency.capitalize()}", WAYS_TO_EARN[currency]))
        else:
            await message.send(embed=errorMsg(f"{currency.capitalize()} is not a valid currency!\nIt must be either Credits, Unity, or Gems"))
