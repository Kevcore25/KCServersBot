import discord
from discord.ext import commands
from calculatefuncs import *
class AccountUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(
        help = f"Change your account settings",
        aliases = ['setting', 'options']
    )
    async def settings(self, message, option: str = None, *, value: str | int | bool = None):
        user = User(message.author.id)

        options: dict[str, bool | int | str] = user.getData("settings")

        vaildOptions = ["publicity", "IGN", "AI", "password"]

        if option is None:
            embed = discord.Embed(
                title = "Account settings",
                description = f"These are your account settings. You can change them by: running `{prefix}settings [(ID of option) <value>]`",
                color = 0x00AAFF
            )
            
            # Public account
            embed.add_field(
                name=f"Public Account (ID: `publicity`): {options.get('publicity', True)}", 
                value=f"Whether your account can be viewed when another user passes an argument for the following commands: `account`, `graphbalance`, `baljson`.\nDefaults to True (On).",
                inline=False
            )
                
            # MC IGN
            embed.add_field(
                name=f"Minecraft Username (ID: `IGN`): {options.get('IGN', None)}", 
                value=f"Your Minecraft username. This is required in order to exchange into KCash.\nThe username must be registered on KMCExtract!",
                inline=False
            )
            
            # Automation
            embed.add_field(
                name=f"Account Automation (ID: `AI`): {options.get('AI', False)}", 
                value=f"Whether your account will periodically run the following commands on its own: `daily`, `work`.\nThe automation is not a set period and can run at anytime.\nAutomated commands will appear in the <#{botsettings['AI Channel']}> channel.\nDefaults to False (Off).\n**This feature will not be available until V.5.0!**",
                inline=False
            )
                
            # Password
            pw = options.get("password", "None")
            embed.add_field(
                name=f"Password (ID: `password`): {pw if pw == 'None' else ('*' * len(pw))}", 
                value=f"The password used for the future *Web KCServers Game*, allowing you to play without Discord.\nIf the password is set to None, this feature is disabled.\nIf this feature is enabled, `baljson` will no longer work on your account.\nDefaults to None\n-# **Please use an insecure password! The security of this can be easily breached**",
                inline=False
            )

        elif value is None:
            embed = errorMsg("A value must be specified!")
        
        else:
            value = "".join(value)

            if option in vaildOptions:
                if value.isdigit(): value = int(value)
                elif value.lower() == "on": value = True
                elif value.lower() == "off": value = False

                options[option] = value

                user.setValue("settings", options)

                embed = successMsg(description=f"Changed the value of `{option}` to `{value}`")

            else:
                embed = errorMsg("Must be a vaild option!\nDid you type the ID of the option instead of its name?")

        await message.send(embed=embed)

    @commands.command(
        help = f"Force an account update",
        description = """Sometimes your account may be missing some valves. This command will make sure to find missing values and fix them. Corruptted values may not be fixed.""",
        aliases = ['fixaccount']
    )
    async def fix(self, message):
        user = User(message.author.id)
        result = user.update()
        await message.send(
                f"Your account data has been updated to the newest version!" if result else (
                f"The account updater did not make any changes to your account data. If you believe your account has an error, please contact the owner."
            )
        )

        
    @commands.command(
        name = 'ign',
        help = f"Set MC Username.\nFormat: {prefix}ign <MC Username>"
    )
    async def set_ign(self, message, ign = None):
        if ign is None:
            embed = discord.Embed(title="Failed",description=f"Minecraft username not specified!", color=0xFF0000)
            await message.send(embed=embed)
        else:    
            await self.settings(message, "IGN", value=(ign,))

    @commands.command(
        help = f"Get your current score",
        description = f"""Factors that affect score:
    - Ranking on leaderboard ((11 - current) ^ 1.2. Cannot be under 0)
    - Average Credits earned ((1/20) * (Avg. Credits). Cannot be over 50)
    - Amount of transactions (sqrt(transactions/2). Cannot be over 50)
    - Average Unity earned ((1/5) * (Avg. Unity))
    - KCash Exchanged (1/500 * (KCash Exchanged). Cannot be over 20)"""
    )
    async def score(self, message, user: discord.Member = None):
        if user is None:
            u = User(message.author.id)
        else:
            u = User(user.id)

        totalscore, reason = calcScore(u, msg=True) 

        embed = discord.Embed(title="Score Calculation",description=f"""## Total Score: `{totalscore}`\n## Reasons:\n{reason}\n\nScore determines who wins before a reset.\nThe top 5 scores gain `Gems` which will be kept for the next reset.\nAfter a reset, the following keys will be resetted:\n credits, unity, items, job, rob, bs%, kcashExchanged, log, players""", color=0xFF00FF)
        await message.send(embed=embed)


    @commands.command(
        help = "Redeems a gift code",
        aliases = ['redeemcode', 'redeemgift'],
        description = "You can redeem a gift code to get rewards! A redeem code can only be used once per account"
    )
    @commands.cooldown(2, 10, commands.BucketType.user) 
    async def redeem(self, message, *, code: str):
        u = User(message.author.id)

        # Get gift codes
        try:
            with open("giftcodes.json", "r") as f:
                codes = json.load(f)
        except FileNotFoundError:
            with open('giftcodes.json', 'w') as f:
                f.write("{}")
            codes = {}

        try: # You can also use if code in list
            # Reset CD. CD is for failure attempts
            self.redeem.reset_cooldown(message)
            
            credits, unity, gems, uses = codes[code]

            # Check if the code is already used
            if code in u.getData("redeemedCodes"):
                await message.send(embed=errorMsg(f"You already redeemed the code `{code}`!"))
                return


            # Delete if uses is 0
            uses -= 1
            if uses <= 0:
                del codes[code]
            else:
                codes[code] = [credits, unity, gems, uses]
                
            with open("giftcodes.json", 'w') as f:
                json.dump(codes, f, indent=4)

            # Append code to account so they cannot use again
            redeemed = u.getData('redeemedCodes')
            redeemed.append(code)
            u.setValue('redeemedCodes', redeemed)

            # Add balances
            u.addBalance(credits=credits, unity=unity, gems=gems)

            # Send MSG
            await message.send(embed=successMsg("Code redeemed!", 
                f"You obtained:" +
                (f"\n  `{'+' if credits > 0 else ''}{credits} Credits`" if credits != 0 else "") + 
                (f"\n  `{'+' if unity > 0 else ''}{unity} Unity`" if unity != 0 else "") + 
                (f"\n  `{'+' if gems > 0 else ''}{gems} Gems`" if gems != 0 else "")
            ))

        except KeyError:
            await message.send(embed=errorMsg(f"The code `{code}` does not exist, or has ran out of uses!"))

        
    @commands.command(
        help = f"Send someone Credits. Format: {prefix}send <user> <amount>",
        description = """There is a fee and your target will only receive 90% of the amount"""
    )
    @commands.cooldown(1, 30, commands.BucketType.user) 
    async def send(self, message, target: discord.Member, amount: float):
        user = User(message.author.id)
        data = user.getData()

        amount = round(float(amount), 2)

        if amount > data['credits']:
            await message.send(embed=errorMsg("Amount is less than your balance!")); return
        
        if amount <= 0:
            await message.send(embed=errorMsg("Amount cannot be 0 or under!")); return
        
        if target == message.author:
            await message.send(embed=errorMsg("Cannot send yourself money!")); return

        
        targetUser = User(target.id)
        
        getAmount = round(amount * .9, 2)

        user.addBalance(
            credits=-amount,
        )
        targetUser.addBalance(
            credits=getAmount,
        )

        embed = successMsg("Successfully sent", f"Sent {target.mention} `{getAmount} Credits`")
        await message.send(embed=embed)

        
    @commands.command(
        help = f"Send someone Gems",
        description = """There is absoultely no fee for sending someone gems!\nBack and forth exchanges are prohibited at all costs.""",
        aliases = ["sg"]
    )
    @commands.cooldown(1, 30, commands.BucketType.user) 
    async def sendgems(self, message, target: discord.Member, amount: float):
        user = User(message.author.id)
        data = user.getData()

        amount = int(amount)

        if amount > data['gems']:
            await message.send(embed=errorMsg("Amount is less than your balance!")); return
        
        if amount <= 0:
            await message.send(embed=errorMsg("Amount cannot be 0 or under!")); return
        
        if target == message.author:
            await message.send(embed=errorMsg("Cannot send yourself money!")); return

        targetUser = User(target.id)
        
        user.addBalance(gems=-amount)
        targetUser.addBalance(gems=amount)

        embed = successMsg("Successfully sent", f"Sent {target.mention} `{amount} Gems`")
        await message.send(embed=embed)
         
    @commands.command(
        help = f"Create a DM",
        description = """Creates a direct message where you are able to use some, but not all commands.\nIt is mainly for usecases such as `redeem` where things may want to be privated.\n`account` (or bal) command is slightly broken - it is unable to calculate the statuses properly.""",
        aliases = ["dm"]
    )
    async def createdm(self, message):
        user = message.author

        await user.create_dm()
        await user.send(embed=successMsg(title="Created a DM channel!", description="""This is a DM channel, mainly used for private commands such as `settings`, `redeem`, `account`.\nSome commands may not work properly and some commands are disabled."""))