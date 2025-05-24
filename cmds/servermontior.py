from discord.ext import commands
from calculatefuncs import *

from mcstatus import JavaServer, status_response
MONTIOR_CMDS_DESC = """

-# This command is part of the montioring commands (montior, statusof)"""

SERVER_MONTIOR_DESC = f"""Constantly montiors a server. If the bot detects a change in players, it will notify you about it.\n\nRunning the command again with the same server will remove it.""" + MONTIOR_CMDS_DESC
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

class ServerMontiorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help = f"Status",
        description = GET_STATUS_DESC,
        aliases = ['status', 'getstatus', 'get'],
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
            for address in addresses.replace(" ", "").split(","):
                addServer(address)

        await message.send(embed=embed)

    @commands.command(
        help = f"Server Montior",
        description = SERVER_MONTIOR_DESC,
        aliases = ['servermontior', 'sm'],
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
                return await message.send(embed=successMsg(description=f"Successfully removed `{address}` to your servers list!"))
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
            await message.send(embed=errorMsg(f"The server address `{address}` cannot be fetched!"))

        return await message.send(embed=errorMsg(f"The command cannot be completed."))
