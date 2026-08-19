import discord
from discord.ext import commands
from calculatefuncs import *
import users as UsersFile
import yaml
class AccountUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help = f"Test if you are on your phone, for debug use.",
        hidden = True,
        aliases = ['isonphone', 'checkphone']
    )
    async def isphone(self, message: Context):
        if message.author.is_on_mobile():
            await message.send(f"Yes, you are detected to be using a mobile device.\nStatus: {message.author.mobile_status}")
        else:
            await message.send(f"No, you are detected to be not using a mobile device.\nStatus: {message.author.mobile_status}")
            
    @commands.command(
        help = f"Attempt to fix account problems",
        description = f"""This command attempts to fix some common account problems.\nYou should contact an admin if the error persists even after this command is ran.\nIf there is a valid error, you will gain `1 Gem` for each error as compensation.\n-# The 1 Gem per error must not be abused, such that you may not get a significant amount (over 3) of Gems using the same error message. Gem earnings from abuse are forfeited.""",
        aliases = ['resolveaccount', 'fixaccount', 'restore']
    )
    async def fix(self, message, arg: str = None):
        userTemplate = UsersFile.userTemplate

        fixedProblems = []

        def addInfo(desc: str):
            if desc not in fixedProblems:
                fixedProblems.append(desc)

        # Fix common file errors
        try:
            with open(f"users/{message.author.id}.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            with open(f"users/{message.author.id}.json", "w") as f:
                json.dump(userTemplate, f)
            addInfo("User account not found")
            
        except json.JSONDecodeError:
            if arg == 'restore':
                with open(f"users/{message.author.id}.json", "w") as f:
                    json.dump(userTemplate, f)
                
                addInfo("RESET ACCOUNT TO DEFAULT VALUES")
            else:
                return await message.send(embed=errorMsg(f"Your account data cannot be parsed.\nThis is a serious issue and must be resolved by an admin.\nYou may attempt to run `{prefix}fix restore` to reset your account values back to default values, but this will cause you to lose your progress."))
            
        user = User(message.author.id, doNotCheck=True)
        data = user.getData()

        # Perform a soft user update
        if user.update():
            addInfo("Missing account data keys")

        # Look deeper for the "rob" key
        for k in userTemplate["rob"]:
            if k not in data["rob"]:
                data["rob"][k] = userTemplate['rob'][k]
                addInfo("Rob keys missing")
            elif type(userTemplate['rob'][k]) != data['rob'][k]:
                data["rob"][k] = userTemplate['rob'][k]
                addInfo("Rob key value type incorrect")

        # Ensure job exists
        with open("jobs.yml") as f:
            jobs = yaml.safe_load(f)

        if data['job'] not in jobs:
            data['job'] = jobs[list(jobs)[0]]
            addInfo(f"Job not found; set job to {data['job']}")

        # Check for incorrect item usage
        for name, item in data['items'].items():
            if 'count' not in item:
                item['count'] = 1
                addInfo(f"'count' key not found in item {name}")
            if 'expires' not in item:
                item['expires'] = [-1] * item['count']
                addInfo(f"'expires' key not found in item {name}")
            if 'data' not in item:
                item['data'] = {}
                addInfo(f"'data' key not found in item {name}")

            if item['count'] != len(item['expires']):
                # It is broken anyway, just set it to never expires as compensation 
                item['expires'] = [-1] * item['count']
                addInfo(f'Expiry dates in item {name} is incorrect')

        # Reset some non-crucial keys
        if arg == 'reset':
            for k in {'kcashExchanged', 'tags', 'settings', 'servers', 'playerMonitor', 'lastCG'}:
                data[k] = userTemplate[k]
            addInfo("Reset non-critical keys (no gems awarded)")
            user.addBalance(gems = -1)


        # Save account
        user.saveAccount(data)

        # Final message
        user.addBalance(gems = len(fixedProblems))
        await message.send(embed = basicMsg(title="Account Fixer", description=f"The fixer has fixed {len(fixedProblems)} problems" + (':\n'+'\n- '.join(fixedProblems)) if len(fixedProblems) > 0 else '.') + f'\n\n-# If you still believe something is wrong, you should contact an admin, or try running `{prefix}fix reset` to reset the values of non-critical keys (your balances/items will be preserved).')

     
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
    - KCash Exchanged (1/5 * (Credits used in KCash Exchange). Cannot be over 2K)
    - Current Unity (5 * Unity)
    
-# Starting in V.9, only the last 5K transactions will be used when calculating average Credits, Unity, etc."""
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
    async def redeem(self, message: Context, *, code: str):
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

            if len(codes[code]) == 4: # Old system without expiry date
                credits, unity, gems, uses = codes[code]
                expiry = -1
            else:
                credits, unity, gems, uses, expiry = codes[code]


            # Check if the code is already used
            if code in u.getData("redeemedCodes"):
                await message.send(embed=errorMsg(f"You already redeemed the code `{code}`!"))
                return

            # Check for expiry
            if expiry != -1 and time.time() > expiry:
                del codes[code]
                with open("giftcodes.json", 'w') as f:
                    json.dump(codes, f, indent=4)
                raise KeyError

            # Delete if uses is 0
            uses -= 1
            if uses <= 0:
                del codes[code]
            else:
                codes[code] = [credits, unity, gems, uses]
                
            with open("giftcodes.json", 'w') as f:
                json.dump(codes, f, indent=4)

            # Append code to account so they cannot use again
            redeemed: list[str] = u.getData('redeemedCodes')
            redeemed.append(code)
            u.setValue('redeemedCodes', redeemed)

            # Add balances
            u.addBalance(credits=credits, unity=unity, gems=gems)

            # Delete user message
            try:
                await message.message.delete()
            except:
                pass

            # Send MSG
            await message.send(embed=successMsg("Code redeemed!", 
                f"{message.author.mention}, you obtained:" +
                (f"\n  `{'+' if credits > 0 else ''}{credits} Credits`" if credits != 0 else "") + 
                (f"\n  `{'+' if unity > 0 else ''}{unity} Unity`" if unity != 0 else "") + 
                (f"\n  `{'+' if gems > 0 else ''}{gems} Gems`" if gems != 0 else "") +
                (f"\n`Nothing`" if credits == unity == gems == 0 else "")
            ))

        except KeyError:
            await message.send(embed=errorMsg(f"The code `{code}` either does not exist, has ran out of uses, or has expired!"))

        
    @commands.command(
        help = f"Send someone Credits. Format: {prefix}send <user> <amount>",
        description = """There is a minor fee of `1 Credit` for each send transaction.\n\n-# **Currency User Interaction Terms:**\n-# Using this command for the purposes of transaction logging is prohibited (that is, to constantly use this command to document transactions in the intent to gain a higher Score value); however, a small amount of this method (under 10 per day) is allowed to give leeway for mistakes. You must only use this for the purpose of sending another user Credits. Additionally, you may not involve real-life currency in exchange for Credits (for example, giving someone Credits in exchange for real-life money). Failure to comply with these terms can result in your balance being subtracted, a balance reset (unless the balance is non-positive), or removal from the game/service."""
    )
    @commands.cooldown(3, 60, commands.BucketType.user) 
    async def send(self, message, target: discord.Member, amount: float):
        user = User(message.author.id)
        data = user.getData()

        amount = round(float(amount), 2)

        if (amount+1) > data['credits']:
            await message.send(embed=errorMsg("Amount is less than your balance!")); return
        
        if amount <= 0:
            await message.send(embed=errorMsg("Amount cannot be 0 or under!")); return
        
        if target == message.author:
            await message.send(embed=errorMsg("Cannot send yourself money!")); return

        
        targetUser = User(target.id)
        
        user.addBalance(
            credits=-(amount+1),
        )
        targetUser.addBalance(
            credits=amount,
        )

        embed = successMsg("Successfully sent", f"Sent {target.mention} `{amount} Credits`\n-# A minor fee of `1 Credit` is deducted from this transaction")
        await message.send(embed=embed)

        
    @commands.command(
        help = f"Send someone Gems",
        description = """Send another user the most precious currency in this game, Gems!\nUnlike sending Credits, there is absolutely no fee for sending another use gems.\n\n-# **Currency User Interaction Terms:**\n-# Using this command for the purposes of transaction logging is prohibited (that is, to constantly send Gems to another user and have that other user return the Gems you sent); however, for the purpose of accounting for mistakes in transactions, this rule can be waived once a day. You must only use this for the purpose of sending another user Gems. Additionally, you may not involve real-life currency in exchange for Gems (for example, giving someone Gems in exchange for real-life money). Failure to comply with these terms can result in your balance being subtracted, a balance reset (unless the balance is non-positive), or removal from the game/service.""",
        aliases = ["sg"]
    )
    @commands.cooldown(1, 30, commands.BucketType.user) 
    async def sendgems(self, message, target: discord.Member, amount: int):
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