import discord
from discord.ext import commands
from calculatefuncs import *

import yaml
class AccountUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(
        help = f"Change your account settings",
        aliases = ['oldsetting', 'oldoptions']
    )
    async def oldsettings(self, message, option: str = None, *, value: str | int | bool = None):
        user = User(message.author.id)

        options: dict[str, bool | int | str] = user.getData("settings")

        vaildOptions = ["publicity", "IGN", "AI", "password"]

        if option is None:
            embed = discord.Embed(
                title = "Account settings",
                description = f"These are your account settings. You can change them by: running `{prefix}oldsettings [(ID of option) <value>]`",
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
        help = f"Change account settings",
        description = f"""This command allows you to change certain values of your account.
It behaves identically to the old command (oldsettings) but with a more robust system.

__How to use__
Run the command without any arguments (`{prefix}settings`) to see a list of settings

Modify a setting by typing `{prefix}setting <option> <value>`, where 
* option: The ID of the setting (e.g. ign)
* value: The new value to be set to

Ensure that the value is valid! Incorrect values may sometimes pass the verification test and give account errors!
""",
        aliases = ['options', 'setting', 'option']            
    )
    @commands.cooldown(10, 3, commands.BucketType.user) 
    async def settings(self, message, option: str = None, *, value: str | int | bool = None):
        u = User(message.author.id)

        # Get all values
        with open('usersettings.yml', 'r') as f:
            settings = yaml.safe_load(f)

        data = u.getData().get('settings', {})

        # Show a list of all commands
        if option is None:
            embed = discord.Embed(
                title = "Account settings",
                description = f"These are your account settings. You can change them by: running `{prefix}settings [(ID of option) <value>]`",
                color = 0x00AAFF
            )

            for id in settings:
                setting = settings[id]

                default = setting['Default']
                values = setting['Values']
                valtype = setting['Type']
                
                if values is None:
                    if valtype == "str": values = "Any text"
                    if valtype == "bool": values = "true, false"
                    if valtype == "int": values = "Any integer"
                    if valtype == "float": values = "Any integer or decimal"
                else:
                    values = ', '.join(str(i) for i in values)

                # Add field
                embed.add_field(
                    name=f"{setting['Name']} (ID: `{id}`): {data.get(id, default)}", 
                    value=f"{setting['Description']}-# Type: {valtype} | Values: {values} | Default: {default}",
                    inline=False
                )

            # Send embed
            await message.send(embed=embed)

        else:
            # This means to modify data

            # Check if option exists
            option = option.lower().strip()

            if option not in settings:
                await message.send(embed=errorMsg(f"The specified option (`{option}`) is not valid!\nEnsure you are using the ID instead of the full name of the option."))
                return
        
            setting = settings[option]

            # Check if value exists
            # Only for BOOL type, this flips the option
            if value is None:
                if setting['Type'] == "bool":
                    data[option] = not data.get(option, setting['Default'])
                    # Save
                    u.setValue('settings', data)
                    await message.send(embed=successMsg(description = f"Changed the value of {setting['Name']} ({option}) to `{data[option]}`"))

                else:
                    await message.send(embed=errorMsg("You must specify a value!\nOnly bool type settings do not require a value."))

            else:
                # Ensure it is typed correctly
                # This only applies if the VALUES is NOT null
                if setting['Values'] is not None:
                    value = value.lower()
                    if value not in setting['Values']:
                        await message.send(embed=errorMsg(f"You must specify a valid value!\nPossible values are: {', '.join('`' + str(i) + '`' for i in setting['Values'])}"))
                        return
                    # Otherwise, just continue

                # Check if it is valid
                match setting['Type']:
                    case "bool":
                        if value.lower() in ('on', 'true', 'yes', 'enable'):
                            value = True
                        elif value.lower() in ('off', 'false', 'no', 'disable'):
                            value = False
                        else:
                            await message.send(embed=errorMsg("The value must be a valid boolean expression!\nFor example, typing `yes`, `on`, or `true` will enable the setting while something such as `false` will disable it."))
                            return
                        
                    case "int":
                        if not value.lstrip('-').isdigit():
                            await message.send(embed=errorMsg("The value must be a valid integer expression!\nFor example, you can use values such as `1` but not `abc`"))
                            return
                        
                    case "float":
                        if not value.lstrip('-').replace('.', '').isdigit() or value.count('.') > 1:
                            await message.send(embed=errorMsg("The value must be a valid decimal expression!\nFor example, you can use values such as `-1.2` or `1` but not `abc`"))
                            return
                    # Do nothing for STR

                # Save
                data[option] = value
                u.setValue('settings', data)
                await message.send(embed=successMsg(description = f"Changed the value of {setting['Name']} ({option}) to `{data[option]}`"))

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
            f"The account updater did not make any changes to your account data. If you believe your account has an error, please contact an administator."
        ))

        
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
    - Ranking on leaderboard ((6 - current) * 200. Cannot be under 0)
    - Average Credits earned (2 * (Avg. Credits). Cannot be over 5K)
    - Amount of transactions (sqrt(transactions/2) * 100. Cannot be over 5K)
    - Average Unity earned (10 * (Avg. Unity))
    - KCash Exchanged (1/5 * (KCash Exchanged). Cannot be over 2K)
    - Current Unity (5 * Unity)"""
    )
    async def score(self, message, user: discord.Member = None):
        if user is None:
            u = User(message.author.id)
        else:
            u = User(user.id)

        totalscore, reason = calcScore(u, msg=True) 

        embed = discord.Embed(title="Score Calculation",description=f"""## Total Score: `{totalscore}`\n## Reasons:\n{reason}\n\nScore determines who wins before a reset.\nThe top 3 scores gain `Gems` which will be kept for the next reset.\nAfter a reset, the following keys will be resetted:\n credits, unity, items, job, rob, bs%, kcashExchanged, log, players""", color=0xFF00FF)
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

        # Delete user message
        await message.delete()

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