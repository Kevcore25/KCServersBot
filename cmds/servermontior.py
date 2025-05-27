from discord.ext import commands, tasks
from calculatefuncs import *
from mcstatus import JavaServer, status_response
MONTIOR_CMDS_DESC = """

-# This command is part of the montioring commands (montior, statusof, and addplayer)"""

SERVER_MONTIOR_DESC = f"""Adds a server to be montiored.\n\nRunning the command again with the same server will remove it.""" + MONTIOR_CMDS_DESC
PLAYER_MONTIOR_DESC = f"""Constantly montiors the server that you have added to see if a specified player has joined/left.""" + MONTIOR_CMDS_DESC
GET_STATUS_DESC = f"""Obtain the status of a server. If no arguments are specified, it will fetch the servers you specified in the `montior` command""" + MONTIOR_CMDS_DESC

def returnStatusObj(address: str, timeout: int = 1) -> JavaServer:
    return JavaServer.lookup(address, timeout)

def SmartServName(status: status_response.JavaStatusResponse) -> str:
    """
    Attempts to get the server's name based on the MOTD using an alghorithm
    """

    motd = status.motd.to_minecraft()
    sym = r"§"

    motd = motd.strip()
    motd = motd.replace("\n", sym)

    if motd.startswith(sym):
        for i in range(len(motd)):
            if motd[i] == sym and not motd[i+2] == sym:
                return motd[i+2:].split(sym)[0].strip()
        
    elif sym in motd:
        return motd.split(sym)[0]

    else:
        return motd
    
def parse(player: str):
    return player.replace("_", "\\_")

class ServerMontiorCog(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.fetchServers.start()

        self.lastServerPlayers = {}

    @tasks.loop(seconds=20)
    async def fetchServers(self):
        """Fetches servers from users. Uses a more optimized algorithm than the previous"""
        # ASSUMES: Only one player can be in 1 server.

        storedServers: dict[str, status_response.JavaStatusResponse] = {}
        errorServers: list[str] = [] # Servers that errored (e.g. connection error)

        for userfile in os.listdir('users'):
            userid = userfile.replace(".json", "")

            embed = discord.Embed(
                title = "Player Notification",
                color = 0xFF00FF
            )

            currentPlayers = []

            try:
                with open(os.path.join("users", userfile), "r") as f:
                    data = json.load(f)

                # Add lastPlayers if empty
                if userid not in self.lastServerPlayers:
                    self.lastServerPlayers[userid] = {}

                if "servers" in data and "playerMontior" in data: 
                    if "*" in data["playerMontior"]:
                        allPlayers = true
                    else:
                        allPlayers = false

                    for server in data['servers']:
                        try:
                            if server not in storedServers:
                                storedServers[server] = returnStatusObj(server).status()

                            # Get name of server
                            name = SmartServName(storedServers[server])
                            if name == '':
                                name = server
                            else:
                                name += f" ({server})"

                            # Get Players
                            # EDGECASE: No players
                            if not (storedServers[server].players.online == 0 or storedServers[server].players.sample is None):
                                for player in storedServers[server].players.sample:
                                    if player.name in data['playerMontior'] or allPlayers:
                                        # Add current players
                                        if player.name not in currentPlayers:
                                            currentPlayers.append((name, player.name))
                            else:
                                currentPlayers.append((name, ""))

                        except Exception as e: 
                            errorServers.append(server)
                            print(e)
                
                # Only send if it is not empty,
                # AND if the players changed
                if currentPlayers != self.lastServerPlayers[userid]:
                    # Convert to dictionary
                    serverPlayers: dict[str, list[str]] = {}
                    for server, player in currentPlayers:
                        if server not in serverPlayers:
                            serverPlayers[server] = []
                        if player != "":
                            serverPlayers[server].append(player)

                    lastServerPlayers = self.lastServerPlayers[userid]
                    # Determine joins
                    for server, players in serverPlayers.items():
                        # Do not calc errored servers
                        nocalc = false
                        for s in errorServers:
                            if s in server:
                                nocalc = true
                                break
                        if nocalc: continue

                        tempPlayers = []

                        if server not in lastServerPlayers:
                            lastServerPlayers[server] = []

                        for player in players:
                            # Player is not in the last fetch
                            if player not in lastServerPlayers[server]:
                                tempPlayers.append(parse(player) + " joined")

                        # If last - current 
                        # IN [abc, def], def leaves
                        # [abc, def] - [abc] = [def]
                        # leave =def
                        for player in set(lastServerPlayers[server]) - set(players):
                            if player in data['playerMontior'] or allPlayers:
                                tempPlayers.append(player + " left")

                        if len(tempPlayers) > 0:
                            embed.add_field(name = server + ":", value = "\n".join(tempPlayers), inline=False)

                    # Update lastPlayers
                    self.lastServerPlayers[userid] = serverPlayers

                    # Don't send if empty
                    if len(embed.fields) > 0:
                        # Send message
                        user = await self.bot.fetch_user(userid)

                        await user.create_dm()
                        await user.send(embed=embed)

            except Exception as e: 
                print(e)

    @commands.command(
        help = f"Status",
        description = GET_STATUS_DESC,
        aliases = ['status', 'getstatus', 'get', 'fetch'],
    )
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def statusof(self, message, addresses: str = None):
        user = User(message.author.id)

        embed = discord.Embed(
            title="Server statuses",
            color=0xFF00FF
        )

        def addServer(addr: str):
            server = returnStatusObj(addr)
            
            try:
                status = server.status()                
                
                name = SmartServName(status)

                if name == '':
                    name = addr
                else:
                    name += f" ({addr})"

                if status.players.online > 0:
                    players = ", ".join(player.name for player in status.players.sample)
                else:
                    players = "No players online"

                desc = f"""```ansi\n{status.motd.to_ansi()}```\n**Players ({status.players.online}/{status.players.max}):**\n""" + players + f"\n-# Version: `{status.version.name}` | Latency: `{round(status.latency)} ms`"

                embed.add_field(
                    name = name,
                    value = desc,
                    inline = false
                )
            except Exception as e:
                embed.add_field(
                    name = addr, 
                    value = "Unable to get the server status: " + str(e),
                    inline = false
                )
                
        if addresses is None:
            for addr in user.getData("servers"):
                addServer(addr)

        else:
            if len(addresses.split(",")) > 5:
                return await message.send(embed=errorMsg(f"You can only fetch up to a maximum of 5 servers at a time!"))

            for address in addresses.split(","):
                addServer(address)

        await message.send(embed=embed)

    @commands.command(
        help = f"Server Montior",
        description = SERVER_MONTIOR_DESC,
        aliases = ['servermontior', 'sm', 'addserver', 'addserv', 'track'],
    )
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def montior(self, message, address: str = None):
        user = User(message.author.id)
        
        # Check for server argument
        if address is None:
            return await message.send(embed=errorMsg("You must specify a valid server address!"))

        # Determine if the server already is on the user list.
        # If it is, instead of adding it, remove it.
        # It also means the program does not need to fetch the server to see if it is valid or not.
        if address in user.getData("servers"):
            if user.removeValue("servers", address):
                return await message.send(embed=successMsg(description=f"Successfully removed `{address}` from your servers list!"))
            else:
                return await message.send(embed=errorMsg(f"Cannot remove the address from your account!"))

        # Max 5 statuses
        if len(user.getData("servers")) >= 5:
            return await message.send(embed=errorMsg(f"You can only have a maximum of 5 servers for your account!"))

        # Check if the entered server is valid by fetching the status
        server = returnStatusObj(address)

        try:
            status = server.status()
            status.latency

            # Must be a valid server
            if user.appendValue("servers", address):
                return await message.send(embed=successMsg(description=f"Successfully added `{address}` to your servers list!"))

        except (ConnectionRefusedError, ConnectionError, TimeoutError):
            return await message.send(embed=errorMsg(f"The server address `{address}` cannot be fetched!"))

        return await message.send(embed=errorMsg(f"The command cannot be completed."))
    
    @commands.command(
        help = f"Player Montior",
        description = PLAYER_MONTIOR_DESC,
        aliases = ['pm', "playermontior", "removeplayer"], # Add remove player alias because it DOES remove the player
    )
    async def addplayer(self, message, ign: str = None):
        user = User(message.author.id)
        
        # Check for IGN argument
        if ign is None:
            return await message.send(embed=errorMsg("You must specify a valid Minecraft username!"))

        # Determine if the IGN is already on the list
        if ign in user.getData("playerMontior"):
            if user.removeValue("playerMontior", ign):
                return await message.send(embed=successMsg(description=f"Successfully removed `{ign}` from your players list!"))
            else:
                return await message.send(embed=errorMsg(f"Cannot remove that player from your account!"))

        # Max 100
        if len(user.getData("playerMontior")) >= 100:
            return await message.send(embed=errorMsg(f"You can only have a maximum of 100 players for your account!"))

        if user.appendValue("playerMontior", ign):
            return await message.send(embed=successMsg(description=f"Successfully added `{ign}` to your players watchlist!"))

        return await message.send(embed=errorMsg(f"The command cannot be completed."))
    