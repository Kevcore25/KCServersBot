import discord
from discord.ext import commands
from calculatefuncs import *
import requests
class AccountViewers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        help = "Displays account stats",
        aliases = ["pf", "profile", "acc", "balance", "bal"]
    )
    async def account(self, message, account: discord.Member = None):
        embed = discord.Embed(
            title = "Account information",
            color = 0xFF00FF
        )
        if account is None:
            account = message.author

        user = User(account.id)

        userData = user.getData()
        options = user.getData('settings')

        # Blocked by user
        if not options.get("publicity", True) and account != message.author: 
            await message.send(embed=errorMsg("The specified user has chosen to hide their profile details!"))
            return

        # Requires Account Viewer for not self
        if account != message.author:
            authoruser = User(message.author.id)
            if authoruser.item_exists("Account Viewer"):
                authoruser.delete_item("Account Viewer")
            else:
                await message.send(embed=errorMsg("You need the Account Viewer item to view other people's balances!"))
                return


        ign = userData['settings'].get("IGN", "None")

        try:
            walletID = userData['LFN']
            if walletID is None:
                raise KeyError
        except KeyError:
            walletID = "Not specified"



        try:
            robrates = userData['rob']['won/lost']

            if (robrates[0] + robrates[1]) == 0: raise KeyError

            robrate = str(round(robrates[0] / (robrates[0] + robrates[1]) * 100, 1)) + "%"
            
        except KeyError:
            robrate = "Unknown"


        embed.add_field(
            name="Balances", 
            value=f"**Credits**: `{numStr(userData['credits'])}`\n**Unity**: `{numStr(userData['unity'])}/{300 if user.item_exists('Unity Increase') else 200}`\n**Gems**: `{int(userData['gems']):>,}`"
        )
        embed.add_field(
            name="KCMC Info", 
            value=f"**MC Username**: `{ign}`\n**KCash**: *`Obtaining data...`*"
        )
        if not isDM(message):
            embed.add_field(
                name="Rob Stats", 
                value=f"**Rob Attack**: `{calculateRobAttack(account)} Lvls`\n**Rob Defense**: `{calculateRobDefense(account)} Lvls`\n**Success rate**: `{robrate}`\n**Insights**: `{userData['rob']['insights']}/3`"
            )
        else:
            embed.add_field(
                name="Rob Stats (Restricted in DM channel)", 
                value=f"**Rob Attack**: `? Lvls`\n**Rob Defense**: `? Lvls`\n**Success rate**: `{robrate}`\n**Insights**: `{userData['rob']['insights']}/3`"
            )
        embed.add_field(
            name=f"Credit Perks (~{calcCredit(100, user)}%)", 
            value=calcCreditTxt(user),
            inline=False
        )

        itemsTxt = []

        with open('shop.json', 'r') as f:
            shopitems = json.load(f)

        # Items
        for id, item in userData['items'].items():
            try:
                itemsTxt.append(
                    f"**{id}** ({item['count']}/{shopitems[id]['limit']})" + ": " + 
                    (f"Expires <t:{round(item['expires'][0])}:R>" if item['expires'][0] != -1 else "Never expires")
                )
            except KeyError:
                itemsTxt.append(
                    f"**{id}**" + ": " + 
                    (f"Expires <t:{round(item['expires'][0])}:R>" if item['expires'][0] != -1 else "Never expires")
                )

        embed.add_field(
            name=f"Items", 
            value="\n".join(itemsTxt if itemsTxt != [] else ["No items"]),
            inline=False
        )
        embed.add_field(
            name="Other Info", 
            value=f"**Wealth Power**: `Calculating...`\n**Bot Stock%**: `{userData['bs%']}`\n**Score**: `Calculating...`",
            inline=False
        )

        msg = await message.send(embed=embed)


        # Get KCash 

        try:    
            with open(os.path.join(KMCExtractLocation, "users.json"), 'r') as f:
                kmceusers = json.load(f)
        
            kcash = kmceusers[ign]['KCash']
        except KeyError:
            kcash = "Not registered"
        except:
            kcash = "Error"

        embed.set_field_at(
            index = 1,
            name="KCMC Info", 
            value=f"**MC Username**: `{ign}`\n**KCash**: `{kcash}`"
        )    
        embed.set_field_at(
            index = 5,
            name="Other Info", 
            value=f"**Wealth**: `{numStr(calcWealth(user))}`\n**Wealth Power**: `{calcWealthPower(user)}%`\n**Bot Stock%**: `{userData['bs%']}`\n**Score**: `{numStr(calcScore(user))}`",
            inline=False
        )

        # # Add KCash notice
        # embed.set_footer(text="A new global KCash server will be up later.")

        await msg.edit(embed=embed)

    

    @commands.command(
        help = "Displays account stats",
        aliases = ['jsonbal', 'jb', 'bj'],
        hidden = True
    )
    async def baljson(self, message, account: discord.Member = None):
        embed = discord.Embed(
            title = "Account information in JSON",
            color = 0xFF00FF
        )
        if account is None:
            account = message.author

        user = User(account.id)

        userData = user.getData()
        options = user.getData('settings')

        # Blocked by user
        if not options.get("publicity", True) and account != message.author: 
            await message.send(embed=errorMsg("The specified user has chosen to hide their profile details!"))
            return

        # Has password
        if options.get("password", "None") != "None": 
            await message.send(embed=errorMsg("Cannot view this user's JSON file!"))
            return
        
        # Requires Account Viewer for not self
        if account != message.author:
            authoruser = User(message.author.id)
            if authoruser.item_exists("Account Viewer"):
                authoruser.delete_item("Account Viewer")
            else:
                await message.send(embed=errorMsg("You need the Account Viewer item to view other people's balances!"))
                return

        
        embed.description = "```json\n" + json.dumps(userData, indent=4) + "```"

        await message.send(embed=embed)
        
    @commands.command(
        name = 'lfn',
        help = f"Set LFN Wallet ID (username).\nFormat: {prefix}lfn <Wallet ID (username)>",
        description = f"LFN (L.F. Network) is part of KCServers. Therefore, this bot also has that feature.\nBy setting down a Wallet ID, the bot can check for the stats of the username using the LFN API. Send features will not be implemented.",
        aliases = ["set_lfn", "set_wallet"]
    )
    async def lfn(self, message, walletID = None):
        user = User(message.author.id)

        
        if walletID is None:
            embed = discord.Embed(title="Failed",description=f"Wallet ID is not specified!", color=0xFF0000)
        else:

            r =  requests.post(f"http://192.168.1.71:218/?type=profile&WalletID={walletID}", timeout=2)
            try:
                r.json() # Check if response is JSON
                walletID = walletID.replace("\\", "")

                if user.setValue('LFN', walletID):
                    embed = discord.Embed(title="Success",description=f"Your LFN Wallet ID is now set to `{walletID}`", color=0x00FF00)
                else:
                    embed = discord.Embed(title="Failed",description=f"An unknown error occurred while trying to set your LFN Wallet ID. Try running the command again", color=0xFF0000)
            except requests.JSONDecodeError:
                embed = discord.Embed(title="Failed",description=f"LFN returned: {r.text}", color=0xFF0000)

        await message.send(embed=embed)