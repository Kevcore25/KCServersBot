"""
PIP REQUIREMENTS:
pip install requests mcstatus discord.py names matplotlib scipy python-dotenv
"""
print("Importing libraries")
import discord, json, random, time, traceback, names, re, datetime, pytz
from discord.ext import commands, tasks
import time, os, sys, threading, dns, requests, asyncio, math
import dns.resolver
from mcstatus import JavaServer
from users import User
import users as usersFile
from games import CrashGame, Players
import games
import bisect
import matplotlib.dates as mdates
from traceback import print_exc as printError
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from dotenv import load_dotenv
from calculatefuncs import *
print("Finished importing")
load_dotenv()

WAYS_TO_EARN = {
    "credits": ("""
### Recommended
1. **Jobs**: Apply for a job to earn rewards every hour.
2. **Daily**: You can claim a daily reward for free every 12 hours.
3. **Skill Games**: Games such as *MC Hangman* and *Gofish* prioritizes skill rather than gambling.
4. **Beg**: Beg for a high chance at getting Credits.
### Other ways 
5. **Gambling Games**: Games such as *Crash Game* are high-risk, high-reward.
6. **Rob**: Rob other players for a chance to earn some of their Credits.
7. **Exchange**: Exchange Gems into Credits.     
-# *Higher Wealth Powers can result in some features of the bot giving less rewards.*
-# *Make sure to maximize your Credit Perks before gambling for best results!*
"""),
    "unity": ("""
### Recommended
1. **Jobs**: Apply for a job to earn rewards every hour.
2. **Daily**: You can claim a daily reward for free every 12 hours.
### Other ways 
3. **Exchange**: Exchange Gems into Unity.     
-# *Higher Wealth Powers can result in some features of the bot giving less rewards.*
"""),
    "gems": ("""
### All ways
1. **Events**: Limited-time events can give Gems as rewards. Be sure to participate in them!
2. **Resets**: Periodically, balance resets happen, and Gems are given as compensation for the top 3 players in Credits.
""")
}


with open("botsettings.json", 'r') as f:
    data = json.load(f)

    KMCExtractLocation = data['KMCExtract']
    prefix = data['prefix']
    inflationAmt = data['inflation amount']
    adminUsers = data['admins']
    botAIChannel = data['AI Channel']
    serverID = data['Server ID']

activity = discord.Activity(type=discord.ActivityType.watching, name=f"KCMC Servers (V.4.0)")
bot = commands.Bot(
    command_prefix=[prefix], 
    case_insensitive=True, 
    activity=activity, 
    status=discord.Status.online,
    intents=discord.Intents().all()
)




botactive = 0


# Notice: Due to the KCash server going offline until a new server is opened, this command will not be running
@tasks.loop(seconds = 60)
async def kcashEarningLoop():
    # t = threading.Timer(60, kcashEarningLoop)
    # t.daemon = True
    # t.start()
    try:

        with open(KMCExtractLocation + "/users.json", 'r') as f:
            kmceusers = json.load(f)
        with open('pingservers.json', 'r') as f:
            data = json.load(f)

        for user, serverIP in data.items():
            if serverIP.lower() == "none": continue

            try:
                # if ":" in serverIP:
                #     port = int(serverIP.split(':')[1])
                # else:
                #     port = 25565
                
                #print(serverIP)
                ss = JavaServer.lookup(serverIP, timeout = 0.125)
                server = ss.status()
                # server = JavaServer.lookup(serverIP, timeout=1).status()
            except (TimeoutError, ConnectionError, dns.resolver.LifetimeTimeout) as e:
                print(f"Connection Error: {serverIP}")
                continue
            
            # Remove unity
            user = User(user)
            if user.getData('unity') <= 0:
                continue

            user.addBalance(unity = -0.01)

            if server.players.sample is not None:
                for player in server.players.sample:
                    
                    if player.name in kmceusers:
                        kmceusers[player.name]['KCash'] += 3
                        print(f"{player.name} got 3 kcash")
                
        with open(KMCExtractLocation + "\\users.json", 'w') as f:
            json.dump(kmceusers, f)        
    except:
        printError()

previousba = 0

def statusloop():
    threading.Timer(300, statusloop).start()
    try:
        # Define the MST timezone
        mst_timezone = pytz.timezone('US/Mountain')

        # Get the current time in UTC
        utc_now = datetime.datetime.now(pytz.utc)

        # Convert the current time to MST
        mst_now = utc_now.astimezone(mst_timezone)

        # Extract hour, minute, and day of the week
        hour_of_day = mst_now.hour
        minute_of_hour = mst_now.minute
        day_of_week = mst_now.weekday()  # 0 = Monday, 6 = Sunday

        # Print the results
        # print(f"Hour of Day: {hour_of_day}")
        # print(f"Minute of Hour: {minute_of_hour}")
        # print(f"Day of Week: {day_of_week} (0 = Monday, 6 = Sunday)")
        with open("userschedules.json", 'r') as f:
            data = json.load(f)

        for user in bot.get_guild(serverID).members:
            u = str(user.id)
            if u not in data:
                data[u] = {"day": [], "hr": [], "min": [], "status": []}
            
            data[u]['day'].append(day_of_week)
            data[u]['min'].append(minute_of_hour)
            data[u]['hr'].append(hour_of_day)
            
            if user.status in [discord.Status.dnd, discord.Status.online]:
                status = 1
            else:
                status = 0
            
            data[u]['status'].append(status)

        with open("userschedules.json", 'w') as f:
            json.dump(data, f)
    except:
        printError()

@tasks.loop(seconds = 3)
async def botAI():
    #threading.Timer(1, await botAI, args=[id]).start()

    global botactive, previousba
    # Passives

    # for b in ("bot1", "bot2"):
    #     await subBotAI(b)
    
    user = bot.user.id


    u = User(user)
    data = u.getData()

    credits, unity, gems = data['credits'], data['unity'], data['gems']

    def get_user(user: str):
        with open(f"users/{user}.json", "r") as f:
            return json.load(f) 
    
        
    channel = bot.get_channel(botAIChannel)

    # Commands
    async def run(command, **args):
        try:

            try:
                message = await channel.send(f"""[[Main bot]](http://DEBUG/ActiveState:{botactive}/Chance:{round(1 / (106 - botactive * 5) * 100 if botactive > 0 else 0.2, 2)}%) {prefix}{command} {' '.join((f'"{i}"' if ' ' in str(i) else str(i)) for i in args.values())}""")
            except:
                printError()
                message = await channel.send(f"[BOT] {prefix}{command}")

            ctx = await bot.get_context(message)
            return await ctx.invoke(bot.get_command(command), **args)
        except:
            printError()

    # Daily
    if (time.time() - data["dailyTime"] > 60*60*12) and (random.randint(0,99) == 0):
        await run('daily')
    # Hourly
    if time.time() - data["hourlyTime"] > 60*60:
        await run('hourly')

    # Determine the chance based on botactive
    if botactive > 0:
        r = random.randint(0, (105 - botactive * 5))
    else:
        r = random.randint(0, 499)

    if botactive >= 1: botactive -= 1

    # if previousba != botactive:
    #     #await channel.edit(topic = f'**Mute Channel NOW!** | Active State: {botactive} ({round(1 / (106 - botactive * 5) * 100, 2)}%/10 sec) | This is how the economy will break, how inflation occurs, how everyone quits')

    previousba = botactive


    match r:
      #  case 0: await rob()
        case 1: 
            for i in range(2): 
                if credits >= 0: await run('beg')
        case 2: 
            if round(credits / 100) > 0: 
                await run('crashgame', betamount = round(credits/100 if credits < 10000 else 100), autocash = random.randint(11, 20) / 10)
       # case 3: (await run('beg') for i in range(2))
        case _:
            pass
        


    # When balance is negative, give the bot some starting money
    if credits <= 0: await run('set', key="credits", value = 100)
    

@bot.event
async def on_ready():    
    usersFile.botID = str(bot.user.id)
    print("Ready, starting loops")

    statusloop()

    await botAI.start()
    await kcashEarningLoop.start()
    print("Ready!")


@bot.event
async def on_message(message: discord.Message):
    global botactive
    await bot.process_commands(message)

    content = message.content

    if content.startswith(prefix):
        botactive += 5
        if botactive > 20:
            botactive = 20







@bot.command(
    help = "Displays account stats",
    aliases = ['jsonbal', 'jb', 'bj'],
    hidden = True
)
async def baljson(message, account: discord.Member = None):
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
    
    embed.description = "```json\n" + json.dumps(userData, indent=4) + "```"

    await message.send(embed=embed)


@bot.command(
    help = "Displays account stats",
    aliases = ["pf", "profile", "acc", "balance", "bal"]
)
async def account(message, account: discord.Member = None):
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
        value=f"**Credits**: `{numStr(userData['credits'])}`\n**Unity**: `{numStr(userData['unity'])}/200`\n**Gems**: `{int(userData['gems']):>,}`"
    )
    embed.add_field(
        name="KCMC Info", 
        value=f"**MC Username**: `{ign}`\n**KCash**: *`Obtaining data...`*"
    )
    embed.add_field(
        name="Rob Stats", 
        value=f"**Rob Attack**: `{calculateRobAttack(account)} Lvls`\n**Rob Defense**: `{calculateRobDefense(account)} Lvls`\n**Success rate**: `{robrate}`\n**Insights**: `{userData['rob']['insights']}/3`"
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
        value=f"**Wealth Power**: `{calcWealthPower(user)}%`\n**Bot Stock%**: `{userData['bs%']}`\n**Score**: `{numStr(calcScore(user))}`",
        inline=False
    )

    # # Add KCash notice
    # embed.set_footer(text="A new global KCash server will be up later.")

    await msg.edit(embed=embed)


@bot.command(
    help = f"Change your account settings",
    aliases = ['setting', 'options']
)
async def settings(message, option: str = None, *, value: str | int | bool = None):
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

@bot.command(
    help = f"Force an account update",
    description = """Sometimes your account may be missing some valves. This command will make sure to find missing values and fix them. Corruptted values may not be fixed.""",
    aliases = ['fixaccount']
)
async def fix(message):
    user = User(message.author.id)
    result = user.update()
    await message.send(
            f"Your account data has been updated to the newest version!" if result else (
            f"The account updater did not make any changes to your account data. If you believe your account has an error, please contact the owner."
        )
    )

@bot.command(
    help = "Display the people with the most Credits",
    aliases = ["lb"]
)
async def leaderboard(message):
    embed = discord.Embed(
        title = "Top members with the most Credits",
        color = 0xFF00FF
    )

    usersDir = os.listdir('users')

    users = {}
    for file in usersDir:
        if file == "main.json": continue
        with open('users/' + file, 'r') as f:
            try:
                data = json.load(f)
                c = float(data['credits'])
                if c != 0 and data.get('settings', {}).get("publicity", True): users[file.replace(".json", '')] = c
            except: pass

    totalCredits = 0

    sortedUsers = sorted(users.items(), key=lambda x:x[1], reverse=True)

    for i in range(len(sortedUsers)):
        try:
            usr = sortedUsers[i]

            user = bot.get_user(int(usr[0]))

            totalCredits += usr[1]
            try:
                embed.add_field(name=f"{i + 1}. {user.display_name}", value=f"Credits: {numStr(usr[1])}")
            except AttributeError:
                embed.add_field(name=f"{i + 1}. Unknown", value=f"Credits: {numStr(usr[1])}")
        except Exception as e:
            embed.add_field(name=f"{i + 1}. Error", value=f"Reason: {e}")

    # Inflation % = Total Credits of Members / (Inflation amount * Amount of Members) x 100 (%)
    inflationLvl = totalCredits / (inflationAmt * (i+1)) * 100
    if inflationLvl < 100: inflationLvl = 100

    # Average credits = total / number of users
    avgcredits = totalCredits / (i+1)

    embed.description = f"**Total Credits**: `{numStr(totalCredits)}`\n**Inflation**: `{round(calcInflation() * 100)}%`\n**Average Credits**: `{numStr(avgcredits)}`"

    await message.send(embed=embed)

@bot.command(
    help = "Display the people with the most Credits",
    aliases = ["lbs", 'slb', 'leaderboardscore']
)
async def scoreleaderboard(message):
    embed = discord.Embed(
        title = "Top members with the most score",
        color = 0xFF00FF
    )

    usersDir = os.listdir('balanceLogs')

    users = {}
    for file in usersDir:
        if file == "main": continue

        if data.get('settings', {}).get("publicity", True): 
            users[file.replace(".json", '')] = calcScore(User(file.replace(".json", '')))

    totalCredits = 0

    sortedUsers = sorted(users.items(), key=lambda x:x[1], reverse=True)

    for i in range(len(sortedUsers)):
        try:
            usr = sortedUsers[i]

            user = bot.get_user(int(usr[0]))

            totalCredits += usr[1]
            try:
                embed.add_field(name=f"{i + 1}. {user.display_name}", value=f"Score: {numStr(usr[1])}")
            except AttributeError:
                embed.add_field(name=f"{i + 1}. Unknown", value=f"Score: {numStr(usr[1])}")
        except Exception as e:
            embed.add_field(name=f"{i + 1}. Error", value=f"Reason: {e}")

    # Average credits = total / number of users
    avgcredits = totalCredits / (i+1)

    embed.description = f"**Average Score**: `{numStr(avgcredits)}`"

    await message.send(embed=embed)

@bot.command(
    name = "about",
    help = "About the bot",
    aliases = ["info", "information", "botinfo"]
)
async def botinfo(message):
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


@bot.command(
    name = 'ign',
    help = f"Set MC Username.\nFormat: {prefix}ign <MC Username>"
)
async def set_ign(message, ign = None):
    user = User(message.author.id)

    
    if ign is None:
        embed = discord.Embed(title="Failed",description=f"Minecraft username not specified!", color=0xFF0000)
        await message.send(embed=embed)

    else:    
        await settings(message, "IGN", value=(ign,))
    



@bot.command(
    name = 'lfn',
    help = f"Set LFN Wallet ID (username).\nFormat: {prefix}lfn <Wallet ID (username)>",
    description = f"LFN (L.F. Network) is part of KCServers. Therefore, this bot also has that feature.\nBy setting down a Wallet ID, the bot can check for the stats of the username using the LFN API. Send features will not be implemented.",
    aliases = ["set_lfn", "set_wallet"]
)
async def lfn(message, walletID = None):
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



    
@bot.command(
    help = f"Get hourly reward",
    description = """The hourly reward increases Credit earnings for 10 minutes"""
)
async def hourly(message):
    user = User(message.author.id)
    data = user.getData()

    if 'hourlyTime' not in data:
        data["hourlyTime"] = 0

    if time.time() - data["hourlyTime"] < 60*60:
        embed = discord.Embed(title="On Cooldown!",description=f"You can claim the hourly reward <t:{int(data['dailyTime'] + 60*60)}:R>", color=0xFF0000)
        await message.send(embed=embed)
        return
    
    success = user.setValue("hourlyTime", int(time.time()))
    
    if success:      
        embed = discord.Embed(title="Hourly reward",description=f"Thank you for checking in with the bot!\nYou received a +10% Credits earning perk for 10 minutes", color=0x00FF00)
  
    else:
        embed = discord.Embed(title="An error occurred!",description=f"An unknown error occurred. Please try running the command again.", color=0xFF0000)


    await message.send(embed=embed)


    
@bot.command(
    help = f"Send someone Credits. Format: {prefix}send <user> <amount>",
    description = """There is a fee and your target will only receive 90% of the amount"""
)
@commands.cooldown(1, 30, commands.BucketType.user) 
async def send(message, target: discord.Member, amount: float):
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
    success = targetUser.addBalance(
        credits=getAmount,
    )

    if success:      
        embed = successMsg("Successfully sent", f"Sent {target.mention} `{getAmount} Credits`")
  
    else:
        embed = discord.Embed(title="An error occurred!",description=f"An unknown error occurred. Please try running the command again.", color=0xFF0000)


    await message.send(embed=embed)


    
@bot.command(
    help = f"Get daily reward",
    description = """The daily reward gives an amount of Unity as well as Credits that scales with your wealth power.\nThe more wealth power you have, the less you earn.\nThe command be ran every 12 hours"""
)
async def daily(message):
    user = User(message.author.id)
    data = user.getData()
    if time.time() - data["dailyTime"] < 60*60*12:
        embed = discord.Embed(title="On Cooldown!",description=f"You can claim the daily reward <t:{int(data['dailyTime'] + 60*60*12)}:R>", color=0xFF0000)
        await message.send(embed=embed)
        return


    amount = 50 / (calcWealthPower(user, True) / 5)
    unityAmt = 3


    if random.randint(0,9) > 0:
        success = user.addBalance(
            credits=amount,
            unity=unityAmt
        )
        if success:      
            user.setValue('dailyTime', int(time.time()))
            user.saveAccount()
            embed = discord.Embed(title="Daily reward",description=f"Thank you for checking in with the bot!\nYour rewards:\n`+{numStr(amount)} Credits`\n`+{numStr(unityAmt)} Unity`", color=0x00FF00)
    
        else:
            embed = discord.Embed(title="An error occurred!",description=f"An unknown error occurred. Please try running the command again.", color=0xFF0000)
    else:
        user.setValue('dailyTime', int(time.time()) + 3720)
        user.saveAccount()
        credLost = calcWealthPower(user) / 2
        embed = discord.Embed(title="Daily failure",description=f"Where does the daily money come from?\nWhen you run the daily command, you actually take money away from the bot. Credits do not get created typically unless it is from the bot itself; you take the bot's money instead\nToday, the bot has decided to **rob** you instead of letting you steal it, making you lose `{numStr(credLost)} Credits` but gain `{numStr(unityAmt * 3 + 1)} Unity`.\nThe daily CD is also increased by 10%", color=0xFF0000)
        user.addBalance(
            credits=-credLost,
            unity=unityAmt*3 + 1
        )


    await message.send(embed=embed)



@bot.command(
    help = f"Converts Credits into KCash",
    description = f"""Conversion rates can be found by running the command by itself.\n""",
    aliases = ["convert", "change"],
    hidden = True
)
async def exchange(message, amount: float = None):
    user = User(message.author.id)
    data = user.getData()
    inflation = calcInflation()

    with open("botsettings.json", 'r') as f:
        botsettings: dict = json.load(f)
    
    kcashrate = botsettings.get('KCash rate', 0.1)
    exchangeFee = botsettings.get('Exchange fee', [500, 5])

    # Lower exchange rate based on Wealth Power
    try:
        exchangeFee[0] = round(
            (exchangeFee[0] * 2) 
            /
            math.log10(calcWealthPower(user, noperks=True)),
        2)
    except ValueError: # Logarithm of 0
        exchangeFee[0] = 500
        
    # exchange fee cannot be higher than initial
    if exchangeFee[0] > 500: exchangeFee[0] = 500


    if amount is None:
        embed = discord.Embed(title="Exchange information", description=f"""Format: `{prefix}exchange <credits>`\n\nCurrently, it would be `1 Credit` → `{round(kcashrate / inflation, 4)} KCash`\n\n**Exchange fee**: `{exchangeFee[0]} Credits` and `{exchangeFee[1]} Unity` per exchange.""", color=0xFF00FF)
        embed.set_footer(text="Credit exchange fee can be lowered with higher Wealth Power.\nWealth Power perks (e.g. Pacifist) are not taken into account.")

    elif amount <= 0:
        embed = discord.Embed(title="Amount invaild!",description=f"Your amount must be an integer greater than 0!", color=0xFF0000)
    else:
        # Check if user is vaild to exchange
        
        # If amount is more than balance
        if (amount + exchangeFee[0]) > data['credits']:
            embed = discord.Embed(
                title="Not enough Credits!",
                description=f"Your balance is less than the requested exchange amount which requires `{amount + exchangeFee[0]} Credits`!", 
                color=0xFF0000
            )
        # Check unity
        elif data['unity'] < exchangeFee[1]:
            embed = discord.Embed(
                title="Not enough Unity!",
                description=f"Your Unity balance is less than the exchange fee of `{exchangeFee[1]} Unity`!", 
                color=0xFF0000
            )

        else:
            try:
                with open(os.path.join(KMCExtractLocation, "users.json"), 'r') as file:
                    kmceusers = json.load(file)

                ign = user.getData('settings').get("IGN", None)

                getAmount = round(amount * kcashrate, 2)
                kmceusers[ign]['KCash'] += getAmount

                with open(os.path.join(KMCExtractLocation, "users.json"), 'w') as file:
                    kmceusers = json.dump(kmceusers, file)       

                user.addBalance(credits = -amount)

                # Exchange fee
                user.addBalance(credits = -exchangeFee[0], unity = -exchangeFee[1])


                embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} Credits` to `{getAmount} KCash`.\nExchange fee: `{exchangeFee[0]} Credits`, `{exchangeFee[1]} Unity`", color=0x00FF00)

            except KeyError:
                embed = discord.Embed(title="Not registered!",description=f"Your MC Username (`{ign}`) is not registered on KMCExtract!", color=0xFF0000)

    await message.send(embed=embed)

@bot.command(
    help = f"Converts gems into another currency. Run the command by itself for more info.",
    description = f"""Conversion rates can be found by running the command by itself.\nFormat of command: `{prefix} [currency <amount>]`""",
    aliases = ["ge", "gemconvert"]
)
async def gemexchange(message, currency = None, amount = 0):
    user = User(message.author.id)
    data = user.getData()
    
    exchangeRates = {
        ("gems", "unity"): 1,
        ("gems", "credits"): round(50 * calcInflation()),
    }

    if currency is None:
        exchangeRateTxt = "\n".join(f"1 {f} > {exchangeRates[(f,t)]} {t}" for f, t in exchangeRates)
        embed = discord.Embed(title="Exchange information", description=f"""Format: `{prefix}gemexchange [to currency] <amount of gems to exchange>`\n\n**Exchange rates**:\n{exchangeRateTxt}""", color=0xFF00FF)

    elif currency not in ['credits','unity']:
        embed = discord.Embed(title="Not a valid exchange currency!",description=f"Your exchange from currency is not valid! Valid options are credits and unity.", color=0xFF0000)
    elif not str(amount).isnumeric() or int(amount) <= 0:
        embed = discord.Embed(title="Amount invaild!",description=f"Your amount must be an integer greater than 0!", color=0xFF0000)
    else:
    
        for f, t in exchangeRates:
            if f == "gems" and t == currency:
                exchangeRate = exchangeRates[(f,t)]
                if data[f] < amount:
                    embed = discord.Embed(title="Not enough currency!",description=f"Your {f.capitalize()} amount is less than the requested exchange amount which requires {amount}!", color=0xFF0000)
                else:
                    getAmount = round(amount * exchangeRate, 5)

                    if t == "credits":
                        user.addBalance(credits = getAmount, gems = -amount)
                    else:
                        user.addBalance(unity = getAmount, gems = -amount)

                    embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} Gems` into `{getAmount} {t.capitalize()}`", color=0x00FF00)
                break

        else:
            embed = discord.Embed(title="Not a valid exchange currency!",description=f"Your exchange currencies is not valid! Run `{prefix}exchange` to see the details.", color=0xFF0000)


    await message.send(embed=embed)

@bot.command(
    help = f"Get all server statuses",
)
@commands.cooldown(1, 10, commands.BucketType.channel) 
async def servers(message):
   
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

@bot.command(
    help = f"Get your current score",
    description = f"""Factors that affect score:
- Ranking on leaderboard ((11 - current) ^ 1.2. Cannot be under 0)
- Average Credits earned ((1/200) * (Avg. Credits). Cannot be over 50)
- Amount of transactions (sqrt(transactions/2). Cannot be over 50)
- Average Unity earned ((1/5) * (Avg. Unity))"""
)
async def score(message, user: discord.Member = None):
    if user is None:
        u = User(message.author.id)
    else:
        u = User(user.id)

    totalscore, reason = calcScore(u, msg=True) 

    embed = discord.Embed(title="Score Calculation",description=f"""## Total Score: `{totalscore}`\n## Reasons:\n{reason}\n\nScore determines who wins before a reset.\nThe top 5 scores gain `Gems` which will be kept for the next reset.\nAfter a reset, the following keys will be resetted:\n credits, unity, items, job, rob, bs%, helpCmds, log, players""", color=0xFF00FF)
    await message.send(embed=embed)


@bot.command(
    help = f"Beg for money",
    description = """There is a 1/3 Chance of getting caught, resulting in paying 2x of the original win amount.\nThe amount you win is determined by: `(Total Credits/4000 + 20) * randint(5,15)/10 * inflation%` and Wealth Power, where Total Credits is the total amount of credits every user has.\nYou can run this command 3 times in 30 seconds.\nIf you got caught, you will lose 1.75x the win amount (does not get affected by Credit Perks)\nIf you got caught while in debt, you will have to pay `5 Unity` as a fine."""
)
@commands.cooldown(3, 30, commands.BucketType.user) 
async def beg(message, arg=None):
    user = User(message.author.id)
    

    usersDir = os.listdir('users')

    totalCredits = 0

    for file in usersDir:
        with open('users/' + file, 'r') as f:
            totalCredits += json.load(f)['credits']

    winAmount = round((totalCredits/4000 + 20) * random.randint(5,15)/10 * calcInflation(), 2)

    winAmount = round(winAmount / (1 + calcWealthPower(user)/100), 2)

    r = random.randint(0,2)
                    
    # Add a warning if user is too in debt
    if user.getData('unity') < -50 and arg is None:
        await message.send(embed=errorMsg(f"You are running low on unity and should be saving up with commands such as daily.\nA high negative unity can be hard to recover and provides lower amounts of begging money.\nYou may choose ignore this warning by running this command with any arguments (e.g. `{prefix}beg ignore`)"))
        return

    if r == 0:
        if user.getData('credits') < 0:
            user.addBalance(unity = -5)

            embed = discord.Embed(title="You got caught!",description=f"You got caught by the police!\nYou did not have anymore Credits, so you paid the police `5 Unity`.", color=0xFF0000)

        else:
            loseAmount = round(winAmount * 1.75, 3)

            user.addBalance(credits = -loseAmount)

            embed = discord.Embed(title="You got caught!",description=f"You got caught by the police!\nAs a result, you paid the police `{numStr(loseAmount)} Credits`.", color=0xFF0000)

    else:
        winAmount = calcCredit(winAmount, user)
        user.addBalance(credits = winAmount)

        embed = discord.Embed(title="Begging successful!",description=f"{names.get_first_name()} gave you `{numStr(winAmount)} Credits`.", color=0x00FF00)

    await message.send(embed=embed)

@bot.command(
    help = f"Rob someone the modern way.\nFormat: {prefix}rob <target>",
    description = """
A new modern robbing system that rolls values instead of a fixed 33% to win.
    
**Dice Roll System**
This robbing system rolls a dice from 1 to a set amount. If your dice roll is higher than the opponent's roll, you win the rob. Otherwise, you lose the rob.
If you rolled the same as your target, a reroll is done.
By default with no upgrades or whatsoever, your Rob Attack has a level of 5, and your Rob Defense has a level of 5. This means that while robbing someone, you can roll up to a number of 5.
Certain actions and job professions can increase your Rob Attack and Rob Defense levels.

While robbing, the difference between the amount of money you have increases the target's Rob Defenses by a certain amount. 
The equation of this additional Defense gain is modelled by the equations: 
- _`(Target's RDL) * ((Target Balance) / (User Balance) / 1.5) ^ 2`_
- _`(Target's RDL) * ((User Balance) / (Target Balance) / 1.75) ^ 2`_
The highest value of the two equations will be used as the additional Defense gain.
The additional Defense gain cannot be below 1 and the final Defense Level will be rounded to the nearest integer.

Also when failing a rob, you gain an *Insight*, increasing your chances of suceeding at the cost of your rob defenses decreasing.
Insights can stack up to 3 times and reset when succeeding a rob or being successfully robbed by another.

**Additional factors**
* Target is offline or idle: Target Defense Rob -1
* Already robbed that target within 5 minutes: Target Defense Rob +2
* Has an Insight: Rob Attack +1 but Rob Defense -1 (Stacks up to 3 times)
target
Essentially, it is way easier for the target to gain Rob Defenses than it is for you to gain Rob Attacks, making it harder for you to successfully rob someone.

**Locks and Lock Picks**
If the target has a `Lock`, you cannot rob that target unless you have a `Lock Pick`.
Lock picks have a 75% of bypassing a lock, and a 25% of getting caught.
If you bypass the lock, it is not over, and you still have to win the rob.
If you do not bypass, your lock pick will be confiscated.

**Amounts**
Win Amount: 
The amount you earn by successfully robbing someone is based on a percentage of the target's balance.
The amount will be subtracted from the target's balance and will be given to you.
Amount you earn: ||*`(Target's Balance) / 10`*||

Lose Amount:
The amount you lose by failing to rob someone is based on a percentage of your balance and the target's balance.
You may go into debt if there is a large balance difference between you and the target.
Amount you lose: ||*`(Your Balance) / 20 + (Target's Balance) / 15`*||
""",
    aliases = ["newrob"]
)
@commands.cooldown(1, 30, commands.BucketType.user) 
async def rob(message, target: discord.Member, ignorewarn = None):
    # This code should be cleaned up later
    # It is much more effective to use a class instead of functions within functions

    user = User(message.author.id)
    targetUser = User(target.id)

    if user.getData()['credits'] < 0:
        embed = discord.Embed(title="An error occurred!",description=f"Cannot rob when your balance is under 0!", color=0xFF0000)
        await message.send(embed=embed)
        rob.reset_cooldown(message)
        return
    if targetUser.getData()['credits'] < 0:
        embed = discord.Embed(title="An error occurred!",description=f"Cannot rob when the target's balance is under 0!", color=0xFF0000)
        await message.send(embed=embed)
        rob.reset_cooldown(message)
        return
    if target == message.author:
        embed = discord.Embed(title="An error occurred!",description=f"Cannot rob yourself!", color=0xFF0000)
        await message.send(embed=embed)
        rob.reset_cooldown(message)
        return

    # Get variables
    userBal = user.getData()['credits']
    targetBal = targetUser.getData()['credits']

    # Get amounts
    winAmount = round(targetBal / 10, 2)
    loseAmount = round((userBal / 20) + (targetBal / 15), 2)

    userRAL = calculateRobAttack(message.author)
    targetRDL = calculateRobDefense(target)

    # Additional target RDL
    try:
        diff = ((targetBal / userBal) / 1.5) ** 2
    except ZeroDivisionError:
        diff = 10001
    try:
        diff2 = ((userBal / targetBal) / 1.75) ** 2
    except ZeroDivisionError:
        diff2 = 10001

    # if higher, use diff2
    if diff2 > diff: diff = diff2

    if diff < 1: diff = 1

    targetRDL *= diff
    targetRDL = round(targetRDL)

    # Warn
    if ignorewarn is None and (targetRDL / userRAL) > 3:
        await message.send(embed=discord.Embed(
            title = "Warning",
            description = f"""The target's Rob Defense Level ({targetRDL}) is more than 3x compared to your Rob Attack Level ({userRAL})\nYou are very likely to lose this robbery.\nYou may ignore this warning by running the command with any arguments (e.g. `{prefix}rob {target.global_name} ignore`)""",
            color=0xFFAA00
        ))
        rob.reset_cooldown(message)
        return
    
    msg = await message.send(embed=discord.Embed(
            title = "Rob Results",
            description = f"""Robbing {target.mention}...""",
            color = 0xFF00FF))

    def robGet(u: User, key: str):
        data = u.getData('rob')
        return data[key]
    def robSet(u: User, key: str, value):
        data = u.getData('rob')
        data[key] = value
        u.setValue("rob", data)
    def robAdd(u: User, key: str, value: int):
        data = u.getData('rob')
        data[key] += value
        u.setValue("rob", data)

    def lose():
        # Lose money
        user.addBalance(credits = -loseAmount)
        targetUser.addBalance(credits = loseAmount)

        # Rob stats
        if robGet(user, 'insights') < 3:
            robAdd(user, "insights", 1)

        wl = robGet(user, "won/lost")
        robSet(user, "won/lost", [wl[0], wl[1]+1])

    # Attacked times
    robSet(user, "attackTime", int(time.time()))
    robSet(targetUser, "attackedTime", int(time.time()))

    # Lock
    if targetUser.get_item("Lock", onlydetermine=True): 
        # 75% to break lock if user has lock pick
        if user.get_item("Lock Pick", onlydetermine=True):
            if not random.randint(0,3) == 0:
                em = discord.Embed(
                    title = "Rob Results",
                description = f"""Robbing {target.mention}...

{target.mention} has a lock, but you **successfully picked it!**

Rolling...""",
                    color = 0xFF00FF,
                )

                targetUser.delete_item("Lock")

                await msg.edit(embed=em)
                await asyncio.sleep(3)
            else: 
                em = discord.Embed(
                    title = "Rob Results",
                    description = f"""Robbing {target.mention}...

Unfortunately, {target.mention} has a lock, and the police caught you when you attempted to pick it!
You were fined `{loseAmount} Credits` to {target.mention}""",
                    color = 0xFF0000,
                )
                lose()

                user.delete_item("Lock Pick")

                await msg.edit(embed=em)
                return
        else:
            em = discord.Embed(
                title = "Rob Results",
                description = f"""Robbing {target.mention}...

Unfortunately, {target.mention} has a lock, and you did not bring a lock pick to break it.
You were fined `{loseAmount} Credits` to {target.mention} after the police caught you.""",
                color = 0xFF0000,
            )
            lose()

            await msg.edit(embed=em)
            return
            

    # Logic
    # For loop is for rerolls
    for i in range(10): # Limit 10
        userRoll = random.randint(1, userRAL)
        targetRoll = random.randint(1, targetRDL)
        
        if userRoll == targetRoll: 
            winTxt = f"Close! Rerolling... (Rerolled {i+1} time(s))"
        elif userRoll > targetRoll:
            winTxt = f"You successfully robbed {target.mention} and stole `{winAmount} Credits`!"
            
            # Win Money
            user.addBalance(credits = winAmount)
            targetUser.addBalance(credits = -winAmount)

            # Rob stats
            robSet(user, "insights", 0)
            robSet(targetUser, "insights", 0)

            wl = robGet(user, "won/lost")
            robSet(user, "won/lost", [wl[0]+1, wl[1]])

        elif targetRoll > userRoll:
            match random.randint(1,3):
                case 1: winTxt = f"Unfortunately, {target.mention} caught you and you were forced to pay `{loseAmount} Credits`"
                case 2: winTxt = f"Unfortunately, the Police caught you and you were fined `{loseAmount} Credits` to {target.mention}"
                case 3: winTxt = f"You slipped and fell, causing `{loseAmount} Credits` to be lost after being embarrassed by {target.mention}"

            lose()

        em = discord.Embed(
            title = "Rob Results",
            description = f"""Robbing {target.mention}...

**Your Roll**: `{userRoll}`
**{target.mention}'s Roll**: `{targetRoll}`

**{winTxt}**""",
            color = 0xFF00FF,
        )
        if diff > 1:
            em.set_footer(text = f"Target obtained a +{round((diff-1) * 100)}% in Rob Defense due to differences in Credit balance")

        await msg.edit(embed=em)

        # End if not reroll; otherwise wait 3 sec
        if userRoll != targetRoll:
            break
        else:
            await asyncio.sleep(3)
        

@bot.command(
    help = "Redeems a gift code",
    aliases = ['redeemcode', 'redeemgift'],
    description = "You can redeem a gift code to get rewards! A redeem code can only be used once per account"
)
@commands.cooldown(2, 10, commands.BucketType.user) 
async def redeem(message, *, code: str):
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
        redeem.reset_cooldown(message)
        
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

@bot.command(
    help = "[ADMIN] Creates a gift code",
    hidden = True
)
async def creategift(message: discord.Message, amount: str, uses: int = 1, code: str | None = None):
    # Only admins can use this

    # Amount can be a string like 1C 2U or just 1 2U
    # Ex: !creategift 300 (Creates a random gift code with an amount of 300 credits with 1 use)
    # Or: !creategift "5C 2U" 5 ABCDEF (Creates a gift code with an amount of 5 Credits and 2 Unity with 5 uses)
    # Or: !creategift 100,5U 1 ABCDEF (Creates a gift code with an amount of 100 Credits and 5 Unity with 1 use)

    uses = int(uses)

    if message.author.id in adminUsers:
        # Gen a code
        if code is None:
            code = ''.join(random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]).upper() for i in range(8))

        # Get amounts

        credits = 0
        unity = 0
        gems = 0

        amount = amount.replace(" ", ",").lower()

        tempint = []
        for amt in amount.split(","):
            for t in amt:
                if t.isdigit() or t in ['.', '-']:
                    tempint.append(t)
                else:
                    adding = float("".join(tempint))
                    match t:
                        case "c": 
                            credits += adding
                        case "u":
                            unity += adding
                        case "g":
                            gems += adding
                    tempint = []
                    break # Break out of this so the next values can be entered
        
        # Save gift code
        try:
            with open("giftcodes.json", "r") as f:
                codes = json.load(f)
        except FileNotFoundError:
            with open('giftcodes.json', 'w') as f:
                f.write("{}")
            codes = {}

        codes[code] = [credits, unity, gems, uses]

        with open('giftcodes.json', 'w') as f:
            json.dump(codes, f, indent=4)

        # Send MSG
        await message.send(f"Created a gift code of: `{code}` giving the following: `{credits} Credits`, `{unity} Unity`, and `{gems} Gems`")
    else:
        await message.send("You are not permitted to use this command!")

@bot.command(
    help = f"Add a server to earn KCash.\nFormat: {prefix}addserver [server IP]",
    description = "Using a small amount of unity per minute (0.01), add a server to be a KCash-earning server. The server must have vaild player sample counts, and the player must have the Allow Server Listings set to ON.\nOnly one KCash-earning server is allowed per account. However, __if multiple people are using the same server address, multiple rewards can be obtained__.\nSetting the server to None will disable the feature.\n\nKCash earning server:\nA server, which rewards all online KMCExtract registered players with 3 KCash per minute.",
    aliases = ['setserver']
)
async def addserver(message, server=None):
    # Create an account JYI
    User(message.author.id)

    if server is None:
        embed = discord.Embed(title="Command description:", description = bot.get_command("addserver").description + f"\nFormat: {prefix}addserver [server IP]", color=0xFF00FF)
        await message.send(embed=embed)
        return
    else:

        embed = discord.Embed(title="Please wait...", description = f"The bot is currently trying to fetch the status of `{server}`...", color=0xFF00FF)

        msg = await message.send(embed=embed)
        # Check if the current player count is over 12 or offline

        try:
            if server.lower() != "none":
                if server.startswith('kcservers.ca'):
                    try:
                        serverStatus = JavaServer.lookup(server, timeout=1).status()
                    except (TimeoutError, ConnectionError):
                        server = server.replace("kcservers.ca", "192.168.1.71")
                        serverStatus = JavaServer.lookup(server, timeout=1).status()
                else:
                    serverStatus = JavaServer.lookup(server, timeout=1).status()


            if server.lower() != "none" and serverStatus.players.online > 12:
                embed = discord.Embed(title="Failed", description=f"{server} is not a small server!", color=0xFF0000)

            else:
                with open('pingservers.json', 'r') as f:
                    data = json.load(f)

                data[str(message.author.id)] = server
                embed = discord.Embed(title="Success:", description=f"A KCash-earning server is now set to `{server}`", color=0x00FF00)

                with open('pingservers.json', 'w') as f:
                    json.dump(data, f, indent=4)

        except (ConnectionError, TimeoutError):
            embed = discord.Embed(title="Failed", description=f"`{server}` is offline (timed out)!", color=0xFF0000)

    


        await msg.edit(embed=embed)




@bot.command(
    help = f"Invest money!",
    description = f"""
Invest a portion of your money to the KCServers bot.
The amount you invest cannot exceed 30% of the current bot's balance.

There are 2 formats for this command:
* {prefix}invest <amount> - invests an amount of money to the bot
* {prefix}invest cash - cashes out the money you invested

**How does it work?**
You can invest a portion of your Credits to gain a *Bot Stock Percentage (Or BS%)*.
For example, if the bot has 10000 and you invest 1000, you will get a % equal to (1000 / 11000), which is about 9.09 BS%
In a few days, if the bot balance is now 15000 and you cash out, you will earn 1363.5 Credits, making about $363 gain.

Notice: You must wait at least 5 minutes until you can cash out after investing.
    """,
    aliases = ['stock']
)
@commands.cooldown(1, 600, commands.BucketType.user) 
async def invest(message, arg = "", arg2=''):
    user = User(message.author.id)
    bot = User('main')
    
    botbal = bot.getData('credits')

    try:
        amt = round(float(arg), 2)
        userbal = user.getData('credits')
        if amt > userbal:
            await message.send("You don't have enough Credits to invest that!")
        
        # Fix negative investments
        elif amt <= 0:
            await message.send("You cannot invest negative money!")

        elif amt > 0.3 * botbal:
            await message.send(f"The amount is over 30% of the bot balance! Do something lower than {round(botbal * 0.3, 2)}!")

        else:
            # Check if already investing
            ubs = user.getData('bs%')
            bs = round(amt * 100 / (botbal + amt), 8)

            if ubs != 0 and arg2.lower() != "overwrite":
                await message.send(f"Already investing! Use {prefix}invest cash to cash out or overwrite it by doing {prefix}invest {amt} overwrite")
            # If 0, do not invest to prevent scamming
            elif bs == 0.0:
                await message.send("The amount you invested is too small to gain a BS%!")
            else:

                user.setValue('bs%', bs)
                user.addBalance(credits = -amt) # Bot should also get that balance

                await message.send(f"Invested {amt} Credits for a BS% of {bs * 100}. You must wait at least 10 minutes before cashing out.")

                return # make a CD
    except ValueError:
        if arg.lower() == "cash":
            
            bs = user.getData('bs%')

            if bs == 0:
                await message.send("You don't have an investment right now!")
            else:
                amt = round(botbal * bs / 100, 2) 

                user.addBalance(credits=amt) # bot should also lose that amount

                user.setValue("bs%", 0)

                await message.send(f"Cashed out! You gained {numStr(amt)} Credits!")

        else:
            await message.send("Invaild argument. Must be either: float, 'cash'")

    # Reset CD. CD is only for investments
    invest.reset_cooldown(message)

@bot.command(
    help = f"Own a portion of the bot balance (Scam)",
    description = f"You can own a portion of the bot's balance. When buying a stock, your account will own a % of the bot (Stock%). The maximum Stock% that can be obtained is 30%. When you exchange ({prefix}stock exchange), you will take a % of the bot's balance with a moderate fee. The fee equation is (fee = `(final bot bal - init bot bal) * 0.1`, fee > 0 else fee = 0). Additionally, the % in your account loses value over time (about 0.2% per day but cannot go below 50% of the init Stock%)",
)
async def userstatus(message, member: discord.Member):

    
    match member.status:
        case discord.Status.online:
            onlineStatus = "Online"
        case discord.Status.idle:
            onlineStatus = "Idle"
        case discord.Status.invisible:
            onlineStatus = "Invisible"
        case discord.Status.offline:
            onlineStatus = "Offline"
        case discord.Status.dnd:
            onlineStatus = "Do not disturb"

    await message.send(f"{member.name} is currently {onlineStatus}")
async def msginput(ctx: discord.Message, text: str | None, timeout: int = 60) -> str:
    if text is not None: await ctx.send(text)
    ui = await bot.wait_for("message", check=lambda msg: msg.author == ctx.author, timeout=timeout)
    return str(ui.content)

import games
PLAYER_TIER_COSTS = games.PLAYER_TIER_COSTS

@bot.command(
    name="players",
    help = f"Format: {prefix}players <option>",
    aliases = ['play', 'p', 'mc', 'pop', 'pops']
)
async def players_cmd(message, cmd: str = ".", *args):
    u = Players(
        message.author.id
    )

    if cmd == '.':
        await message.send(embed=discord.Embed(title="Too long to be sent in chat", description="Read the description of the command [here](https://docs.google.com/document/d/1QILQMD5ZxcMeKPrvLbMYo9Yxxsg8DzU_l-IuuV8a4R4/edit?usp=sharing)"))
        return

    command = cmd.split(" ")[0].lower().replace("!","").replace("%","")


    match command:
        case "help" | "?":
            await message.send("Commands: help, mine, popluate, depopulate, populate, loadout, upgrade, bal")
        case "mine": await message.send(u.mine()['text'])
        case "populate" | "popluate":
            
            price = 30 * u.get_overpop()
            if price> u.get_data("food"):
                await message.send("Not enough food!")
            else:
                u.change_value('food', -price)
                await message.send(u.create_pop())
        case "depopulate" | "depopluate": await message.send(u.remove_pop())
        case "loadout": 
            a = {}
            for i in ("armor", "pickaxe", "shields"):

                
                ui = await msginput(message, f"Set default {i} to be ? (Values (tiers): basic, iron, gold, diamond)")
                if ui not in PLAYER_TIER_COSTS:
                    await message.send("Invalid!")
                    return
                else: 
                    a[i] = ui
                    

                
            ui = await msginput(message, f"Set default weapon (tier_[bow, sword, axe]) to be ?")
            if ui.split("_")[0] not in PLAYER_TIER_COSTS and ui.split("_")[1] not in ("bow", "sword", "axe"):
                await message.send("Invalid!")
                return
            else: 
                a['sword'] = ui

            await message.send(u.set_default(a['armor'], a['shields'], a['sword'], a['pickaxe']))
        case "upgrade" | "update": await message.send(u.upgrade())
        case "bal" | "acc" | "pf" | "balance" | "account" | "profile":

            if len(args) > 0:
                userid = bot.get_user(int(args[0].replace("<",'').replace(">",'').replace("@",''))).id
            else:
                userid = message.author.id

            totalFightStr = 0
            totalFightStr2 = 0
            u = Players(userid)
            players = u.get_data('players')
            for player in players:
                dmg = (games.swordDamage[player['sword'].split('_')[0]]) 
                hp = (player['health'] + games.armorDefense[player['armor']] + games.shieldDefense[player['shields']])
                totalFightStr += round((dmg * hp) ** 0.75, 3)
                totalFightStr2 += round((dmg * (player['maxHealth'] + games.armorDefense[player['armor']] + games.shieldDefense[player['shields']])) ** 0.75, 3)


            await message.send(f"""Minerals: {u.get_data("minerals")}\nFood: {u.get_data("food")}\nGold: {u.get_data('gold')}\n\nDefault loadout: ```json\n{json.dumps(u.get_data("defaults"))}```\nTotal Fighting Strength: {get_prefix(totalFightStr, 1)}/{get_prefix(totalFightStr2, 1)}""")
        case "players" | "p":

            
            p = args[0] if len(args) > 0 else None
            players = u.get_data('players')

            if p is None:

                finalMsg = []
                prange = len(players) if len(players) <= 25 else 25
                for i in range(prange):
                    player = players[i]

                    swordTier = player['sword'].split('_')[0]

                    dmg = (games.swordDamage[swordTier]) 

                    hp = (player['health'] + games.armorDefense[player['armor']] + games.shieldDefense[player['shields']])

                    fightStrength = round((dmg * hp) ** 0.75)

                    atkStr = (PLAYER_TIER_COSTS[swordTier])

                    defStr = (PLAYER_TIER_COSTS[player['armor']] + PLAYER_TIER_COSTS[player['shields']]) // 2
                    mineStr = (PLAYER_TIER_COSTS[player['pickaxe']] * 3)
                    if (atkStr+defStr) - (mineStr * 2) > 80:
                        if atkStr - defStr > 80:
                            designation = "Damager"
                        elif atkStr - defStr < -80:
                            designation = "Tank"
                        else:
                            designation = "Fighter"
                    elif (atkStr+defStr) - (mineStr * 2) < -80:
                        designation = "Miner"
                    else:
                        designation = "General"

                    finalMsg.append(
                        f"Player #{i+1} ({designation}): Fight strength: {fightStrength} | Pick: {player['pickaxe'].capitalize()}"
                    )
                if len(players) > 25: finalMsg.append(f"...+{len(players) - 25} more players")

                await message.send(f"Players:```fix\n" + "\n".join(finalMsg) + "```")
            else:
                # Errors: cannot cast to int, index out of range
                if int(p) > len(players):
                    await message.send("Specified player does not exist!")
                else:
                    player = players[int(p)-1]
                    amr = games.armorDefense[player['armor']]
                    shields = games.shieldDefense[player['shields']]
                    hpStr = (player['health'] + amr + shields)
                    atk = games.swordDamage[player['sword'].split('_')[0]]

                    fightStrength = round((atk * hpStr) ** 0.75, 1)
                    await message.send(
                        f"**Player #{p}**:\nHealth: {player['health']}/{player['maxHealth']}\nArmor: +{amr} ({player['armor'].capitalize()})\nShields: +{shields} ({player['shields'].capitalize()})\nWeapon: {' '.join(player['sword'].split('_')).capitalize()} ({atk} damage per turn)\nPickaxe: {player['pickaxe'].capitalize()} ({int(games.pickaxeMultipliers[player['pickaxe']] * 100)}% mining output)\n\nFighting Strength: {fightStrength}"
                    )
        case "fight" | "kill":

            if len(args) > 0:
                userid = bot.get_user(int(args[0].replace("<",'').replace(">",'').replace("@",''))).id

            else:
                await message.send("Invalid user. Aborting!")
                return

            msg = await message.send("Please wait...")

            fp = games.FightPlayer(
                User(message.author.id),
                User(userid)
            )

            atkerPlayers = fp.atker.get_data('players')
            deferPlayers = fp.defer.get_data('players')
            initatkamt = len(atkerPlayers)
            initdefamt = len(deferPlayers)

            # Add temp stats
            for i in range(len(atkerPlayers)):
                atkerPlayers[i]['hpValues'] = [
                    games.armorDefense[atkerPlayers[i]['armor']],
                    games.shieldDefense[atkerPlayers[i]['shields']]
                ]
            for i in range(len(deferPlayers)):
                deferPlayers[i]['hpValues'] = [
                    games.armorDefense[deferPlayers[i]['armor']],
                    games.shieldDefense[deferPlayers[i]['shields']]
                ]

            for turn in range(100):

                atkerPlayers, deferPlayers = fp.fight(atkerPlayers, deferPlayers)

                astr = fp.calcFightStr2(atkerPlayers)
                dstr = fp.calcFightStr2(deferPlayers)
                
                time.sleep(1)

                await msg.edit(content=f"**Turn {turn}:**\n Attacker Fighting Strength: {round(astr)}\nDefender Fighting Strength: {round(dstr)}\n\nAttacker players: {len(atkerPlayers)}/{initatkamt}\nDefender players: {len(deferPlayers)}/{initdefamt}")

                if astr <= 0 or dstr <= 0:
                    break

            # Clean up temporally values
            for i in range(len(atkerPlayers)):
                del atkerPlayers[i]['hpValues']
            for i in range(len(deferPlayers)):
                del deferPlayers[i]['hpValues']

            # Change player values
            fp.atker.set_value('players', atkerPlayers)
            fp.defer.set_value('players', deferPlayers)

            await message.send(f"User {fp.atker.ID} lost {initatkamt - len(atkerPlayers)} players (Started with {initatkamt})\nUser {fp.defer.ID} lost {initdefamt - len(deferPlayers)} players (Started with {initdefamt})")

        case _:
            await message.send("Command not found")

    
@bot.command(
    help = f"Has aliases for commands relating to Players",
    aliases = ['mine', 'upgrade', 'loadout', 'update', 'depopulate', 'populate', 'fight', 'kill'],
    hidden = True
)
async def players_redir_commands(message: discord.Message):

    await message.send(embed = discord.Embed(
        title = "Unknown command",
        description = f"Did you mean `{prefix}p {message.invoked_with}`?",
        color = 0xFF0000
    ))

@bot.command(
    help = f"Work\nFormat: {prefix}work [apply <job>]",
    description = f"""Apply for a job, then run {prefix}work to earn money. The job you apply for will give you a % increase in work output. The work output is the amount of money you earn from work. The job will also give you a % increase in credit earnings.\nThere is a slight chance (5%) that you will be fired from your job, causing you to lose `10 Unity` (scales with Wealth Power).\nThis 5% of being fired increases as you become more negative in Unity.\nApplying for a job initially costs `5 Unity` (scales with Wealth Power)""",
    aliases = ['job'],
    hidden = True
)
@commands.cooldown(1, 3600, commands.BucketType.user)
async def work(message, cmd = None, value = None):
    user = User(message.author.id)
    data = user.getData()

    # Base gains
    baseCredits = 50 * calcInflation()
    baseUnity = 0.5

    with open('jobs.json', 'r') as f:
        jobs = json.load(f)

    # Get current job
    currentJob = data['job']
    
    if cmd is None:
        embed = discord.Embed(
            title="Work jobs",
            description=(
                f"Apply using `{prefix}work apply <job>`" + 
                ("\n" if currentJob == None else f"\nWork using `{prefix}work work`") +
                "\nWork output is an additional money gain from work.\n" + 
                "\n**Jobs:**\n" + 
                "\n\n".join(f"""**{job}**: {jobs[job]['description']}\nCurrent base rates: `{numStr(baseCredits *(1 + jobs[job]['work output'] / 100))} Credits` and `{numStr(baseUnity * (1 + jobs[job]['work output'] / 100))} Unity`\nPerk: `{"+" + str(jobs[job]['credit perk']) if jobs[job]['credit perk'] >= 0 else jobs[job]['credit perk']}% Credit earnings`""" for job in jobs)
            ), 
            color=0xFF00FF
        )
    elif cmd == "work":

        if currentJob is None:
            embed = errorMsg("You must apply for a job first!")
        else:
            # Amount to fire
            # Should be int(-Unity/10) times, time >= 1, time E I
            fireamt = int(-user.getData('unity')/5)
            if fireamt < 0: fireamt = 1
            for i in range(fireamt):
                if random.randint(0, 19) == 0:
                    # Fired
                    unityLost = 5 * calcWealthPower(user, decimal=True)

                    user.addBalance(unity=-unityLost)
                    user.setValue('job', None)

                    embed = discord.Embed(
                        title="Work",
                        description=(
                            f"Your boss fired you and you no longer have a job anymore!\nYou also lost `{unityLost} Unity`."
                        ),
                        color=0xFF0000
                    )
                    break
            else:
                # Work
                creditGain = calcCredit(baseCredits, user) * (1 + jobs[currentJob]['work output'] / 100)
                unityGain = baseUnity * (1 + jobs[currentJob]['work output'] / 100)

                # Job Bonuses
                if currentJob == "Unifier": unityGain += 0.75
                elif currentJob == "Banker": creditGain += (50 * calcInflation())

                user.addBalance(credits=creditGain, unity=unityGain)

                embed = discord.Embed(
                    title="Work",
                    description=(
                        f"You earned `{numStr(creditGain)} Credits` and `{numStr(unityGain)} Unity` from working as a {currentJob}"
                    ),
                    color=0x00FF00
                )
                # Directly return without resetting the CD
                await message.send(embed=embed)
                return

    elif cmd == "apply":
        # Apply for the job
        value = str(value).title()

        if value in jobs:
            unityLost = 5 * calcWealthPower(user, decimal=True)

            if user.getData('unity') < unityLost:
                embed = errorMsg(title="Not enough balance!", description=f"You don't have enough Unity to apply for a job!\nJob cost: `{unityLost} Unity`\n\n## Tips:{WAYS_TO_EARN['unity']}")
    
            else:

                user.addBalance(unity=-unityLost)
                user.setValue('job', value)

                embed = successMsg("Job applied", f"You paid `{numStr(unityLost)} Unity` to apply for the job of {value}!")

    else: embed = errorMsg("Command is not vaild!")

    await message.send(embed=embed)
    work.reset_cooldown(message)




@bot.command(
    help = f"Play the crash game!",
    description = """This version is modified and split into "rounds" which take about 1 second to update. Each turn has a chance of crashing.""",
    aliases = ['cg', 'crash']
)
@commands.cooldown(1, 300, commands.BucketType.user) 
async def crashgame(message: discord.Message, betamount: float = None, autocash: float = "0"):
    user = User(message.author.id)

    with open("previousCgs.json",'r') as f:
        previousCgs = json.load(f)  
        
    if betamount is None:
 

        plt.xlabel("Game Number")
        plt.ylabel("Ended Multiplier")
        plt.plot(
            range(len(previousCgs)),
            previousCgs
        )
        plt.savefig('temp/cgt.png')
        plt.clf()
        file = discord.File(f"temp/cgt.png", filename=f"cgt.png")
        embed = discord.Embed(
            title = "Previous Multipliers",
            color = 0xFF00FF, 
            description=", ".join(
                (str(round(i, 2))+"x" if i < 5 else (
                    "**"+str(round(i, 2))+"x**" if i < 16 else "***"+str(round(i, 2))+"x***"
                )) for i in previousCgs[-100:] 
            ) + \
            f"\nTotal average: {round(sum(previousCgs) / len(previousCgs), 2)}x multiplier" + \
            f"\nAverage of last 100: {round(sum(previousCgs[-100:]) / len(previousCgs[-100:]), 2)}x multiplier"


        )        
        embed.set_image(url=f"attachment://cgt.png")

        await message.send(file=file, embed=embed)
        crashgame.reset_cooldown(message)
        return
        
   # x = int(input("Enter a number: ")); print("Yay!" if x == 25 else ("NO!" if (str(x) in "".join("-" + str(i) for i in range(100))) else (print("Yes" if (x > 100 and (x > 1000 or x > 10000)) else "Yes...") if x > 10 else (print("No" if x > 5 else "... too small")))))

   
    betamount = round(float(betamount), 2)
    autocash = float(autocash)

    
    if betamount < 0 or betamount > user.getData('credits'):
        await message.send(embed=discord.Embed(description="Invalid bet amount!", color=0xFF0000))
        crashgame.reset_cooldown(message)
        return
    if betamount > 10000:
        await message.send(embed=discord.Embed(description="A maxmium of 10k Credits can be betted!", color=0xFF0000))
        crashgame.reset_cooldown(message)
        return
    user.addBalance(credits=-betamount)

    msg = await message.send(embed=discord.Embed(
        title="Starting...",
        description="Please wait while I set up the game...",
        color = 0xFF00FF,
    ))
    randomNum = random.randint(0,999999)

    cg = CrashGame()

    # Due to credit perks, it should start at a LOWER amount
    cg.multiplier = 0.85
    cg.multipliers = [0.85]

    cashedOut = False

    #plot = cg.create_plot()
    
    xpoints = [0]
    ypoints = [0.85]
    await msg.add_reaction("💰")
    await msg.add_reaction("🛑")

    def check(reaction, user):
        return user == message.author and (str(reaction.emoji) == '💰' or str(reaction.emoji) == '🛑')
    async def cgupdate():
        file = discord.File(f"temp/cg{randomNum}.png", filename=f"cg{randomNum}.png")
        embed = discord.Embed(title = f"Crash Game",color = 0xFF00FF, description="""Press the cash emoji (💰) to cash out.\nPress the stop emoji (🛑) to cash out and/or stop the game.""")        
        embed.set_image(url=f"attachment://cg{randomNum}.png")
        embed.set_footer(text="The only game you can earn so much?!")

        await msg.edit(attachments=[file], embed=embed)

    def p(x = xpoints, y = ypoints, color="b"):
        # create integers from strings
        plt.xlabel("Round")
        plt.ylabel("Multiplier")

        try:
            idx = range(len(x))
            xnew = np.linspace(min(idx), max(idx), 300)

            # interpolation
            spl = make_interp_spline(idx, y, k=2)
            smooth = spl(xnew)

            # plotting, and tick replacement
            plt.plot(xnew, smooth, color)
        except ValueError:
            plt.plot(x,y, color)

        plt.savefig(f"temp/cg{randomNum}.png")
        plt.clf()

    while True:
        try:
            userMsg = await bot.wait_for('reaction_add', timeout=1.5, check=check)

        except (TimeoutError, asyncio.exceptions.TimeoutError):
            pass
        else:
            if not cashedOut:
                
                won = cg.cash_out(betamount)
                actualwon = calcCredit(won, user)
                user.addBalance(credits=actualwon)
                cashedOut = True

                await message.send(f"Won `{won} Credits`! (Actual gained: `{numStr(actualwon - betamount)} Credits`)")
            if str(userMsg[0].emoji) == "🛑":
                plt.title(f"Round {cg.round} | Multiplier: {r['multiplier']}x (Stopped by user)")
                p()
                await cgupdate()
                break
        
        r = cg.next_round()

        if autocash <= float(r['multiplier']) and not cashedOut and autocash != 0:
            won = cg.cash_out(betamount)
            actualwon = calcCredit(won, user)
            user.addBalance(credits=actualwon) # it appears that calccredit is not considered during CG
            cashedOut = True

            await message.send(f"Won {won}! (Autocashed)")             

        if r['crashed']:

            # Precog
            if user.get_item("Precognition") and not cashedOut:
                won = cg.cash_out(betamount)
                actualwon = calcCredit(won, user)
                user.addBalance(credits=actualwon) # it appears that calccredit is not considered during CG
                cashedOut = True

                await message.send(f"**Precognition**: Won `{won} Credits`! (Actual gained: `{numStr(actualwon - betamount)} Credits`)")             

                if user.ID != "main": 
                    user.delete_item("Precognition")

            plt.title(f"Round {cg.round} | Multiplier: {r['multiplier']}x (CRASHED!)")

            xpoints.append(cg.round)
            ypoints.append(0)

            p(color='r')

            await cgupdate()

            break


        xpoints.append(cg.round)
        ypoints.append(r['multiplier'])
        plt.title(f"Round {cg.round} | Multiplier: {r['multiplier']}x")

        p(xpoints, ypoints)

        await cgupdate()
         
    os.remove(f"temp/cg{randomNum}.png")
    crashgame.reset_cooldown(message)

    previousCgs.append(r['multiplier'])
    with open("previousCgs.json",'w') as f:
        json.dump(previousCgs, f)

import questionparser
threading.Thread(target=questionparser.updateTimer).start()


@bot.command(
    help = f"Question",
    description = "Gives a question that when answered correctly, grants you Credits and Unity, but when answered wrong, makes you lose Credits and Unity.\nSpecifiying a subject gives a -90% Credit Earnings for that question.",
    aliases = ['q', 'question']
)
@commands.cooldown(1, 3600, commands.BucketType.user) 
async def questions(message: discord.Message, subject = "RANDOM"):


    u = User(message.author.id)

    if u.getData('job') != "Scholar":
        await message.send("Sorry, but until there are more questions in the bank, I am disabling this command lol good luck with your unity problems")
        questions.reset_cooldown(message)
        return
    subject = str(subject).upper()

    questionsSub = questionparser.sortBySubject()

    if subject == "RANDOM":
        subject = random.choice(list(questionsSub))

    def lost():
        """Loss function"""
        u.addBalance(-creditLoss, -unityLoss)
        
    if subject in questionsSub:

        index = random.choice(questionsSub[subject])

        question = questionparser.questions[index]


        letterNumConv = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}


        ## Grade scaling
        level = int(re.search(r'\d+', question['grade']).group())

        data = u.getData()

        if "grade" in data:
            grade = data['grade']
        else:
            grade = 10 # By default
        
        # Calc grade scaling
        # This should be the formula:
        # WIN REWARD: (Level - Grade) / 10 * 1.5 unless Level is 0 where win reward = +0%
        # LOSE REWARD: (Level - Grade) / 10 * 3 unless Level is 0 where lose reward = -0%
        if level > 0:
            gs_winRwd = round((level - grade) / 10 * 1.5 + 1, 1)
            gs_loseRwd = round((level - grade) / 10 * 3 + 1, 1)
        else:
            gs_winRwd, gs_loseRwd = 1, 1

        creditReward = round(calcCredit(question["creditGain"] * calcInflation() * gs_winRwd, u), 2)
        creditReward = round(creditReward / calcWealthPower(u, decimal=True), 2)

        if subject != "RANDOM": creditReward = round(creditReward / 10, 2)
        unityReward = round(question['unityGain'] / calcWealthPower(u, decimal=True), 2)

        creditLoss = round(question["creditLost"] * calcInflation() / gs_loseRwd, 2)
        unityLoss = round(question['unityLost'], 2)

        
        match subject:
            case "MATH": notice = "The use of GDCs (TI-83/84 Plus) and Desmos is allowed but not any generative source or the internet"
            case "SCIENCE" | "CHEMISTRY" | "PHYSICS": notice = "The use of calculators are allowed but not any generative source or the internet"
            case "ENGLISH": notice = "The use of a dictionary is allowed if specified in the question but not any generative source or the internet"
            case "SOCIAL": notice = "The use of any generative sources or the internet is not allowed"
            case _: notice = "The use of any generative sources or the internet is not allowed"

        ## BIG: If MULTIPLE CHOICE
        if question['options'][0].upper() != "WR":        

            options = {}
            multiplechoices = ["A", "B", "C", "D", "E"]

            # SHUFFLE MULTIPLE CHOICE

            questionOptions = question['options'].copy()            
            
            answer = question['options'][letterNumConv[question['answer']]-1]

            random.shuffle(questionOptions)


            for i in range(len(questionOptions)):
                options[multiplechoices[i]] = questionOptions[i]

            optionsTxt = "\n".join(f"{choice}) {value}" for choice, value in options.items())
            temp = time.time()
            embed = discord.Embed(
                title=f"{subject.capitalize()} Question (ID of {index})",
                description=f"**Multiple Choice** - Level {question['grade']}```fix\n{question['question']}```\n{optionsTxt}\n\nRewards: `{creditReward} Credits`, `{unityReward} Unity`\nLosses: `{creditLoss} Credits`, `{unityLoss} Unity`\n*Expires <t:{int(temp) + question['timelimit']}:R>*",
                color = 0xFF00FF,
            )
            embed.set_footer(text=notice)
            msg = await message.send(embed=embed)
            initTime = time.time()


            optionValues = {"🇦": "A", "🇧": "B", "🇨": "C", "🇩": "D", "🇪": "E"}
            # Add choices
            # await msg.add_reaction("🇦")
            # await msg.add_reaction("🇧")
            # await msg.add_reaction("🇨")
            # await msg.add_reaction("🇩")
            # await msg.add_reaction("🇪")

            for i in range(len(options)):
                await msg.add_reaction(list(optionValues)[i])

            def check(reaction, user):
                return user == message.author and (str(reaction.emoji) in list(optionValues))
            

            try:
                userMsg = await bot.wait_for('reaction_add', timeout=int(temp - initTime + question['timelimit']), check=check)
            except asyncio.exceptions.TimeoutError:
                await msg.edit(embed=errorMsg(f'You lost `{creditLoss} Credits` and `{unityLoss} Unity`!\nYou lost {round(100 / gs_loseRwd-100 , 1)}% less credits because of level scaling.', title="Time limit exceeded!"))
                lost()
                return
            
            userOption = optionValues[str(userMsg[0].emoji)]

            if questionOptions[letterNumConv[userOption]-1] == answer:    
                await msg.clear_reactions()            
                u.addBalance(creditReward, unityReward)
                await msg.edit(embed=successMsg("Correct", f'You gained `{creditReward} Credits` and `{unityLoss} Unity`!\nYou gained {round(100 / gs_winRwd-100 , 1)}% more credits because of level scaling.\nIt took you `{round(time.time() - initTime, 2)} seconds` to answer the question.'))

            else:                
                await msg.clear_reactions()
                await msg.edit(embed=errorMsg(f'You lost `{creditLoss} Credits` and `{unityLoss} Unity`!\nYou lost {round(100 / gs_loseRwd -100 , 1)}% less credits because of level scaling.', title="Wrong!"))
# userOption: {userOption}
# question['options'][letterNumConv[userOption]-1]: {question['options'][letterNumConv[userOption]-1]}
# answer: **{answer}** <- how is this wrong?!?!?!?!? lets do some debugging of JSUT THIS
# ... answer = questionOptions[letterNumConv[question['answer']]-1]
# ...... question['answer']: {question['answer']}
# ...... questionOptions = {questionOptions}
# ...... letterNumConv[question['answer']] = {letterNumConv[question['answer']]} 
# question['options'] (ORIGINAL) = {question['options']}
# options: {options}
# """)
                lost()
        else:
            # IF WRITTEN RESPONSE! NEW CODE
            answer = question['answer']
            temp = time.time()
            embed = discord.Embed(
                title=f"{subject.capitalize()} Question (ID of {index})",
                description=f"**Written Response / Short Answer** - Level {question['grade']}```fix\n{question['question']}```\n*Please send a message with your answer before the time limit expires!*\n\nRewards: `{creditReward} Credits`, `{unityReward} Unity`\nLosses: `{creditLoss} Credits`, `{unityLoss} Unity`\n*Expires <t:{int(temp) + question['timelimit']}:R>*",
                color = 0xFF00FF,
            )
            embed.set_footer(text=notice)

            msg = await message.send(embed=embed)
            initTime = time.time()
            
            try:
                userMsg = await bot.wait_for('message', check=lambda msg: msg.author == message.author, timeout=int(temp - initTime + question['timelimit']))
            except asyncio.exceptions.TimeoutError:
                await msg.clear_reactions()
                await msg.edit(embed=errorMsg(f'You lost `{creditLoss} Credits` and `{unityLoss} Unity`!\nYou lost {round(100 / gs_loseRwd -100, 1)}% less credits because of level scaling.', title="Time limit exceeded!"))
                lost()
                return
           
            if str(userMsg.content).lower().replace(" ","") == str(answer).lower().replace(" ", ""):                     
                await msg.clear_reactions()
                u.addBalance(creditReward, unityReward)
                await msg.edit(embed=successMsg("Correct!",f'You gained `{creditReward} Credits` and `{unityLoss} Unity`!\nYou gained {round(100 / gs_winRwd - 100, 1)}% more credits because of level scaling.\nIt took you `{round(time.time() - initTime, 2)} seconds` to answer the question.'))
            else:                
                await msg.clear_reactions()
                await msg.edit(embed=errorMsg(f'You lost `{creditLoss} Credits` and `{unityLoss} Unity`!\nYou lost {round(100 / gs_loseRwd - 100 , 1)}% less credits because of level scaling.\n{(f"The correct answer starts with `{str(answer)[0]}...` (you answered {userMsg.content})") if len(str(answer)) > 1 else ""}', title="Wrong!"))
                lost()
    else:
        await message.send(embed=errorMsg(f"{subject} is not a vaild subject!\nVaild subjects include: {', '.join(str(i).capitalize() for i in list(questionsSub))}\nNOTICE: Choosing a subject reduces rewards by 75%"))
        questions.reset_cooldown(message)


# Pull MCHangman data from an official source so it is updated once a in while
def pull_mch_data():
    """Pulls data from the MC Property Encyclopedia"""

    # Entity data
    entityData = requests.get("https://joakimthorsen.github.io/MCPropertyEncyclopedia/data/entity_data.json").json().get('key_list')
    # Block data
    blockrawdata = requests.get("https://joakimthorsen.github.io/MCPropertyEncyclopedia/data/block_data.json").json()
    blockData = blockrawdata.get('key_list')
    # Item data
    itemData = requests.get("https://joakimthorsen.github.io/MCPropertyEncyclopedia/data/item_data.json").json().get('key_list')

    # All data
    data = entityData + blockData + itemData

    # Write to file
    with open('mcdata.txt', 'w') as f:
        f.write(
            '\n'.join(data)
        )

    # Also pull for the MCPropertyGuesser game
    with open("mcpgdata.json", 'w') as f:
        json.dump(blockrawdata, f)

# Put in a thread to prevent code stalling
threading.Thread(target=pull_mch_data).start()

@bot.command(
    help = f"Play a simliar version of Hangman",
    description = """A random word will be chosen from a bank. You will have letter attempts and guess attempts. Say a letter to guess a letter, and anything else to guess the word. It costs `8 Credits` to play the game though negative balances are still allowed..\n-# *Data sourced from the [MC Property Encyclopedia](https://joakimthorsen.github.io/MCPropertyEncyclopedia/)*""",
    aliases = ['mch', 'minecrafthangman']
)
@commands.cooldown(1, 30, commands.BucketType.user)
async def mchangman(message: discord.Message):
    u = User(message.author.id)

    # Get data
    with open("mcdata.txt", 'r') as f:
        content = f.read()
    # Parse
    items = []
    for ln in content.splitlines():
        ln = ln.replace("[JE]",'').replace("[BE]",'')
        for i in ("+","-","(","["):
            if i in ln:
                break
        else:
            items.append(ln.strip().lower())

    # Pick a random item
    item: str = random.choice(items)
    item = item#.strip().lower()
    

    # Scramble
    scrambled = []

    guessed = []

    # Attempts and guesses
    attempts = 20 # round(5 + len(item.replace(" ",'')) ** 0.5)
    guesses = 10


    # if 2 + len(set(tuple(item))) < attempts:
    #     attempts = 2 + len(set(tuple(item)))


    for i in item:
        if i == " ": scrambled.append( " ")
        else: scrambled.append("_")

    # Credit formula.
    cred = lambda: round(calcCredit(
        (
            100
            / (32 - attempts - guesses)
            - 1
        ),
     u))
    
    # Subtract 8 credits from user
    u.addBalance(credits=-8)

    # Send MSG
    msg = await message.send(embed=discord.Embed(
        title = "Minecraft Guessing Game",
        description = f"""A random word was chosen from a [bank](https://joakimthorsen.github.io/MCPropertyEncyclopedia/). Say a letter to guess a letter. Type the full word to win.
At anytime in the game, type `exit` to exit out of the game.
Winning will give you `{cred()} Credits`.

**`{' '.join(i for i in scrambled)}`**

Attempts left: `{attempts}`
Word Guesses left: `{guesses}`

Guessed: `{', '.join(guessed if len(guessed) > 0 else (' ',))}`
-# *There is {len(items)} items that the game can choose from*
        """,
        color=0xFF00FF

    ))

    async def edit(text: str):
        await msg.edit(embed=discord.Embed(
            title = "Minecraft Guessing Game",
            description = f"""A random word was chosen from a [bank](https://joakimthorsen.github.io/MCPropertyEncyclopedia/). Say a letter to guess a letter. Type the full word to win.
At anytime in the game, type `exit` to exit out of the game.
Winning will give you `{cred()} Credits`.

**`{' '.join(i for i in scrambled)}`**

Letter Attempts left: `{attempts}`
Word Guesses left: `{guesses}`

Guessed: `{', '.join(guessed)}`
*{text}*""",
            color=0xFF00FF
        ))
    while True:
        try:
            ui = await bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300)
            userInput = ui.content
        except (TimeoutError, asyncio.exceptions.TimeoutError):
            message.send(f"{message.author.mention}, your mc hangman expired after 5 minutes of inactivity!")
            return # Fix potential bug
        userInput = str(userInput).lower()

        # Exit
        if userInput == "exit":
            await edit(f"Exited MCHangman game.") # Makes it BOLD, not italtic
            return
        
        # Already did before
        if userInput in guessed:
            await edit(f"You already guessed that letter!") # Makes it BOLD, not italtic

        # Letter guess
        elif len(userInput) == 1:             
            guessed.append(userInput)
            attempts -= 1

            if userInput in item:
                for i in range(len(item)):
                    if item[i] == userInput:
                        scrambled[i] = userInput
   
                await edit(f"`{userInput}` is in the word!")

                if "_" not in scrambled:
                    c = cred()
                    

                    u.addBalance(c)
                    await edit(f"*You won! You gained `{c} Credits`!*") # Makes it BOLD, not italtic
                    return
                    
            else:
                await edit(f"`{userInput}` is not in the word!")

            if attempts <= 0:
                await edit(f"*You lost! You ran out of attempts! The word was `{item.title()}`*")
                return
        elif userInput == item:            

            c = cred()
            guesses -= 1 #No cred penalty but minus 1 to the counter for edit

            u.addBalance(c)
          
            await edit(f"*You won! You gained `{c} Credits`!*") # Makes it BOLD, not italtic
            mchangman.reset_cooldown(message)
            return
        # Guess wrong
        elif userInput in items:
            guesses -= 1

            if guesses == 0:
                await edit(f"*You lost! You ran out of word guesses! The word was `{item.title()}`*")
                return
            else:
                await edit(f"`{userInput.title()}` is not the word!")
        else:
            continue # Continue the loop
        # One of the if statements ran, so delete author msg
        await ui.delete()


@bot.command(
    help = f"MCPG dictionary",
    description = f"""Format: {prefix}mcd <dictionary>""",
    aliases = ['mcd']
)
async def mcpgdictionary(message: discord.Message, property: str):    
    
    with open("mcpgdata.json", 'r') as f:
        mcpgdata = json.load(f)

    for i in mcpgdata['properties']:
        if mcpgdata['properties'][i]['property_name'].lower() == property:
            try:
                await message.send(mcpgdata['properties'][i]['property_description'])
            except KeyError:
                await message.send("The property has no description 🤷 lol")
            break
    else:
        await message.send("property does not exist")
@bot.command(
    help = f"Play a block property guesser (BETA)",
    description = """A random word will be chosen from a bank. You will have hints and guess attempts to try to guess the block the bot was thinking.\n-# *Data sourced from the [MC Property Encyclopedia](https://joakimthorsen.github.io/MCPropertyEncyclopedia/)*""",
    aliases = ['mcg', 'mcpg', 'mcp']
)
@commands.cooldown(1, 30, commands.BucketType.user)
async def mcpropertyguesser(message: discord.Message):    
    u = User(message.author.id)
    
    with open("mcpgdata.json", 'r') as f:
        mcpgdata = json.load(f)
    # First of all, Choose the WORD
    items = []
    itemslower = []
    for ln in mcpgdata['key_list']:
        for i in ("+","-","(","["):
            if i in ln:
                break
        else:
            items.append(ln.strip())
            itemslower.append(ln.strip().lower())

    block: str = random.choice(items)
    properties = list(mcpgdata['properties'])

    # Remove "tag" properties
    blacklist = ["tag", "face", "collision", "map_color", 'id', 'pathfinding', "placement", "()"]
    for p in properties.copy():
        for blacklisted in blacklist:
            if blacklisted in p:
                try:
                    properties.remove(p)
                except ValueError: pass
    # Now, shuffle the properites. This will be in the order of the hints
    random.shuffle(properties)

    # Now, make a "link" to the properties of the block.
    def get_property(property: str) -> dict[str, str]:
        """Returns into a dict of format:
        {
            name: str (name of property)
            value: str (the value of the property)
        }
        """

        # Link - easier to code
        p = mcpgdata['properties'][property]

        name = p['property_name']

        # Value:
        if block in p['entries']:
            value = p['entries'][block]
            # if dict, means multiple states so combine it into sentences
            if isinstance(value, dict):
                tempstr = []
                for k, v in value.items():
                    tempstr.append(f"{k}: {v}")
                value = ". ".join(tempstr) 
            elif "not updated to" in value.lower() and "(" in value:
                value = value.split("(")[0]
        else:
            value = p['default_value']
        # remove the bracket if it is something like not updated...
       
        
            
        return {"name": name, "value": value}
    
    # Set values
    hints = len(properties) - 10

    # Can choose to use hints but nah this is safer
    currentPropertyIndex = 5

    guesses = 10
    guessed = []

    # Return the properties in string (markdown) format
    def get_current_properties():
        tempstr = []
        for i in range(currentPropertyIndex):
            p = get_property(properties[i])

            tempstr.append(f"**{p['name']}**: {p['value']}")

        return "\n".join(tempstr)
    
    # At this point, most of the code is done so just send msg
    msg = await message.send(embed=discord.Embed(
        title = "Minecraft Block Property Guessing Game",
        description = f"""A random word was chosen from a [bank](https://joakimthorsen.github.io/MCPropertyEncyclopedia/). Say `hint` to get the next property, say `exit` to exit out of this game, or say the name of the block to guess it.

Block Properties:
{get_current_properties()}

Hints left: `{hints}`
Guesses left: `{guesses}`

Guessed: `{', '.join(guessed if len(guessed) > 0 else (' ',))}`
        """,
        color=0xFF00FF
    ))

    async def edit(text: str):
        await msg.edit(embed=discord.Embed(
            title = "Minecraft Block Property Guessing Game",
            description = f"""A random word was chosen from a [bank](https://joakimthorsen.github.io/MCPropertyEncyclopedia/). Say `hint` to get the next property, say `exit` to exit out of this game, or say the name of the block to guess it.

Block Properties:
{get_current_properties()}

Hints left: `{hints}`
Guesses left: `{guesses}`

Guessed: `{', '.join(guessed if len(guessed) > 0 else (' ',))}`

{text}""",
        color=0xFF00FF
        ))
    while True:
        try:
            ui = await bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300)
            userInput = ui.content
        except (TimeoutError, asyncio.exceptions.TimeoutError):
            message.send(f"{message.author.mention}, your mc property guesser expired after 5 minutes of inactivity!")
            return # Fix potential bug
        
        userInput = str(userInput).lower()

        # Exit
        if userInput == "exit":
            await edit(f"Exited MC Property Guesser game. The block was `{block}`") # Makes it BOLD, not italtic
            return
        
        # Already did before
        if userInput in guessed:
            await edit(f"You already guessed that block!") # Makes it BOLD, not italtic

        # hint
        elif userInput == 'hint':             

            if hints > 0:
                hints -= 1
                currentPropertyIndex += 1

                await edit('A property was revealed!')
           
            else:
                await edit(f"You ran out of hints! Guess the block or say `exit` to exit the game.")

           
        elif userInput == block.lower():            

            c = calcCredit(10 + (hints / 2), u)
            guesses -= 1 # minus 1 to the counter for edit
        
            # add money
            u.addBalance(credits=c)

            await edit(f"*You won! You gained `{numStr(c)} Credits`!*") # Makes it BOLD, not italtic
            mcpropertyguesser.reset_cooldown(message)
            return
        
        # Guess wrong
        elif userInput in itemslower:
            guesses -= 1
            guessed.append(userInput)

            if guesses == 0:
                await edit(f"*You lost! You ran out of guesses! The block was `{block.title()}`*")
                return
            else:
                await edit(f"`{userInput.title()}` is not the word!")

        else: continue # Continue the loop

        # One of the if statements ran, so delete author msg
        await ui.delete()



TIME_DURATION_UNITS = (
    ('month', 60*60*24*30),
    ('week', 60*60*24*7),
    ('day', 60*60*24),
    ('hour', 60*60),
    ('min', 60),
    ('sec', 1)
)


def human_time_duration(seconds):
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{} {}{}'.format(amount, unit, "" if amount == 1 else "s"))
    return ', '.join(parts)

@bot.command(
    help = f"Graph your balance changes",
    description = f"""Format: {prefix}oldgraphbalance <user> <timeframe>""",
    aliases = ['ogb', 'oldgraphbal', 'oldbalgraph', 'obg', 'oldbalancegraph']
)
@commands.cooldown(3, 10, commands.BucketType.user) 
async def oldgraphbalance(message: discord.Message, user: discord.Member = None, *, timeframe: str = "1d"):
    # Timeframe. Use KCTimeFrame Format
    timeframe = timeframe.lower().replace(",", " ")

    # Total is in Seconds
    total = 0

    inttemp = []
    skip = False
    for i in range(len(timeframe)):
        t = timeframe[i]

        if t == " ": 
            skip = False
        elif skip:
            continue

        # Is a digit. Record it until a letter is seen
        if t.isdigit():
            inttemp.append(t)
        elif t == " ": 
            continue
        # not a digit. Check for what, like day or month
        else:
            # If empty, just skip
            if len(inttemp) == 0: continue

            timeframetemp = int("".join(inttemp))

            if t == "d": # Days
                timeframetemp *= (60 * 60 * 24)
            elif t == "h": # Hours
                timeframetemp *= (60 * 60) 
            elif t == "m": # Either: minute (more likely so fallback) or month
                # Month. Add a space in case of index errors
                if (timeframe + " ")[i+1] == "o":
                    timeframetemp = int(timeframetemp * (60 * 60 * 24 * 30.5))
                else:
                    timeframetemp *= (60)
            elif t == "w": # Weeks
                timeframetemp *= (60 * 60 * 24 * 7)
            elif t == "y":
                timeframetemp *= (60 * 60 * 24 * 365)
            elif t == "s": # Seconds. Nothing really should happen
                pass
            
            total += timeframetemp
            inttemp = []
            skip = True # Skip until next space
    
    if user is None:
        user = message.author
        userid = message.author.id
    else:
        userid = user.id
        if userid == bot.user.id:
            userid = 'main'

    # Blocked by user
    if not User(userid).getData('settings').get("publicity", True): 
        await message.send(embed=errorMsg("The specified user has chosen to hide their profile details!"))
        return

    # Initialize a list to store the balances
    balances = []
    xstrs = []

    try:
        with open(os.path.join("balanceLogs", str(userid)), 'rb') as f:
            # Move the pointer to the end of the file
            f.seek(0, 2)
            # Get the file size
            size = f.tell()

            tf = "Unknown"

            # Start from the end of the file
            for i in range(size - 1, -1, -1):
                f.seek(i)
                # Read a byte
                char = f.read(1)
                # If it's a newline character and we haven't reached the end of file
                if char == b'\n' and i < size - 1:
                    # Add the line to the list
                    ln = f.readline().decode().rstrip()
                    try:
                        t = int(ln.split(" ")[0])
                    except ValueError: continue

                    if (time.time() - t) > total:
                        break

                    bal = ln.split(" ")[1]
                    balances.append(float(bal))

                    # For string as X value
                    mst = datetime.datetime.fromtimestamp(t, datetime.timezone.utc) - datetime.timedelta(hours=7)

                    # Timeframes. Notice: Again, too much data will override it and it will not be shown
                    # For day (> 1 day) (Probably not shown)
                    if total > (60 * 60 * 24):
                        xstrs.append(mst.strftime("%d"))
                        tf = "Days"
                    else:
                        # For hour time (within a reasonable amount, like <1 day)
                        try:
                            xstrs.append(mst.strftime("%-H:%M"))
                        except ValueError:
                            xstrs.append(mst.strftime("%#H:%M"))
                        tf = "Hourtime"
    except FileNotFoundError:
        await message.send(embed=errorMsg("No balance logs have been recorded!"))
        return 
    
    # If there is only 1 item in the list, nothing will be graphed, so add the same value to the balance.
    if len(balances) == 1:
        balances = balances * 2

    balances.reverse()

    xvalues = [i for i in range(len(balances))]

    xstrs.reverse()
    # If too much data then don't show on graph
    if len(xstrs) < 30:
        plt.xticks(xvalues, xstrs)
    else:
        tf = "Indexes"

    # Create plot
    plt.xlabel(f"Timeframe ({tf})")
    plt.ylabel("Credit Balance")




    plt.title(f"{user.display_name}'s balance changes since {human_time_duration(total)} ago")

    # Slope color
    try:
        first, last = balances[0], balances[-1]
        if first > last: color = 'red'
        elif first < last: color = 'green'
        else: color = 'gray'
    except IndexError:
        color = 'gray'

    plt.plot(xvalues, balances, color=color)

    plt.savefig(f"temp/bal{userid}.png")
    plt.clf()

    file = discord.File(f"temp/bal{userid}.png", filename=f"balanceGraph.png")
    embed = discord.Embed(title="Balance Graph", color=0xFF00FF)
    embed.set_image(url=f"attachment://balanceGraph.png")

    await message.send(file=file, embed=embed)

    os.remove(f"temp/bal{userid}.png")


"""
This is a new experimental balance graph. 
The old one graphs everytime the balance changes. However, this one graphs every x min
Therefore, it is more accurate to the real-world graphs, where you can see the balances every x hour for eaxample.

How does it work?
Initially, it reads the entire balance log up to the specified date. It saves it into a list.
Then, it will begin to plot the balance every x specified by the time.
There will be 100 points, so x can be calculated by every time/100.
Let's go with an example.
Suppose the balance changed at time 12, 35 and 95, with the balance being 50, 100 and 120 respectively.
The user wanted up to time 30. 
It will begin to record the y value as 120 for x = 100, x = 99... x = 95
Then, at x = 94, it will record the balance being 100 up to x = 35
Now, up to x = 0, the y value will be 12 because that is the last value.
If the user wanted up to time 0, because there aren't any other recorded data, we will assume the balance to be 0
So y in x = [0, 11] will be 0.
"""
@bot.command(
    help = f"Graph your balance changes",
    description = f"""Format: {prefix}graphbalance <user> [timeframe] [precision]
user: Member of the user. This can be a @mention
timeframe: The timeframe for the graph. This can be expressed in words, such as "3 days ago" or simply just "3d" or "34s"
precision: A percentage from 1-100 for the precision of points. More points mean more precision. By default, this is 1%
Notice: If the data is too large, precision will be limited to prevent long executions
""",
    aliases = ['gb', 'balgraph', 'graphbal', 'bg', 'balancegraph']
)
@commands.cooldown(2, 10, commands.BucketType.user) 
async def graphbalance(message: discord.Message, user: discord.Member = None, *, timeframe: str = "1d"):
    # Parameter for points
    t = timeframe.split(' ')
    if len(t) > 1 and t[-1].replace(".", '').isdigit():
        precision = float(t[-1])
    else:
        precision = 1


    # Timeframe. Use KCTimeFrame Format
    timeframe = timeframe.lower().replace(",", " ")

    # Total is in Seconds
    total = 0

    inttemp = []
    skip = False
    for i in range(len(timeframe)):
        t = timeframe[i]

        if t == " ": 
            skip = False
        elif skip:
            continue

        # Is a digit. Record it until a letter is seen
        if t.isdigit():
            inttemp.append(t)
        elif t == " ": 
            continue
        # not a digit. Check for what, like day or month
        else:
            # If empty, just skip
            if len(inttemp) == 0: continue

            timeframetemp = int("".join(inttemp))

            if t == "d": # Days
                timeframetemp *= (60 * 60 * 24)
            elif t == "h": # Hours
                timeframetemp *= (60 * 60) 
            elif t == "m": # Either: minute (more likely so fallback) or month
                # Month. Add a space in case of index errors
                if (timeframe + " ")[i+1] == "o":
                    timeframetemp = int(timeframetemp * (60 * 60 * 24 * 30.5))
                else:
                    timeframetemp *= (60)
            elif t == "w": # Weeks
                timeframetemp *= (60 * 60 * 24 * 7)
            elif t == "y":
                timeframetemp *= (60 * 60 * 24 * 365)
            elif t == "s": # Seconds. Nothing really should happen
                pass
            
            total += timeframetemp
            inttemp = []
            skip = True # Skip until next space
    
    if user is None:
        user = message.author
        userid = message.author.id
    else:
        userid = user.id
        if userid == bot.user.id:
            userid = 'main'

    # Blocked by user
    if not User(userid).getData('settings').get("publicity", True): 
        await message.send(embed=errorMsg("The specified user has chosen to hide their profile details!"))
        return

    # Initialize a list to store the balances
    balances = []
    data = []
    try:
        with open(os.path.join("balanceLogs", str(userid)), 'rb') as f:
            # Move the pointer to the end of the file
            f.seek(0, 2)
            # Get the file size
            size = f.tell()
            # Start from the end of the file
            toBreak = False
            for i in range(size - 1, -1, -1):
                if toBreak: break
                f.seek(i)
                # Read a byte
                char = f.read(1)
                # If it's a newline character and we haven't reached the end of file
                if char == b'\n' and i < size - 1:
                    # Add the line to the list
                    ln = f.readline().decode().rstrip()
                    try:
                        t = int(ln.split(" ")[0])
                    except ValueError: continue

                    if (time.time() - t) > total:
                        toBreak = True

                    bal = ln.split(" ")[1]
                    recordedTime = ln.split(" ")[0]
                    # print(recordedTime) 

                    # balances.append(float(bal))
                    # recordedTimes.append(int(recordedTime))
    
                    try:
                        # Convert epoch time to datetime (UTC if needed, use utcfromtimestamp)
                        dt = datetime.datetime.fromtimestamp(int(recordedTime))
                        balance = float(bal)
                        data.append((dt, balance))
                    except ValueError:
                        continue  # Skip lines with invalid numbers
         
    except FileNotFoundError:
        await message.send(embed=errorMsg("No balance logs have been recorded!"))
        return 
   
    data.sort(key=lambda x: x[0])
    def generate_time_points(end_time, window_seconds, interval_seconds):
        """Generates timestamps at intervals within the time window"""

        # Align end_time to the nearest interval
        aligned_timestamp = (int(end_time.timestamp()) // interval_seconds) * interval_seconds
        aligned_end = datetime.datetime.fromtimestamp(aligned_timestamp)
        
        window_delta = datetime.timedelta(seconds=window_seconds)
        interval_delta = datetime.timedelta(seconds=interval_seconds)
        
        time_points = []
        current_time = aligned_end
        while current_time >= (aligned_end - window_delta):
            time_points.append(current_time)
            current_time -= interval_delta
        return time_points[::-1]  # Return oldest first for better bisect behavior

    # Parse data and extract timestamps/balances
    timestamps = [dt for dt, bal in data]
    balances = [bal for dt, bal in data]

    # Init variables for time periods
    totalsec = total       # Total time window to visualize (e.g., 24*3600=24h)

    # If data is too much, do not use that much precision
    maxData = 500
    dataAmt = len(data)
    print(len(data))
    if dataAmt > maxData:
        print("Uh oh, overflow!")
        # Should not exceed maxData points
        # 10000 = totalsec * precision / 100
        # 10000 x 100 / totalsec = precsision

        maxprecision = maxData * 100 * maxData / totalsec
        
        if precision > maxprecision:
            precision = maxprecision

    if precision is None:
        amtOfPoints = 20
    else:
        amtOfPoints = round(totalsec * (precision / 100))
    step = total // amtOfPoints

    # Generate target time points for the graph
    end_time = datetime.datetime.now()
    graph_times = generate_time_points(end_time, totalsec, step)

    # Find the balance at each target time
    graph_balances = []
    for t in graph_times:
        idx = bisect.bisect_right(timestamps, t) - 1
        graph_balances.append(balances[idx] if idx >= 0 else 0.0)
        
    # Slope color
    try:
        first, last = graph_balances[0], graph_balances[-1]
        if first > last: color = 'red'
        elif first < last: color = 'green'
        else: color = 'gray'
    except IndexError:
        color = 'gray'
    # Plotting
    plt.figure(figsize=(12, 6))
    plt.plot(graph_times, graph_balances, linestyle='-', color=color)
    plt.title(f'Balance Over {totalsec//3600}h (Sampled Every {step//3600}h with {round(precision, 5)}% precision*)')
    plt.xlabel('Time')
    plt.ylabel('Balance')

    # Format x-axis based on time window
    time_format = '%m/%d %H:%M' if totalsec <= 86400 else '%m/%d'
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(time_format))
    plt.gcf().autofmt_xdate()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(f"temp/bal{userid}.png")
    plt.clf()

    file = discord.File(f"temp/bal{userid}.png", filename=f"balanceGraph.png")
    embed = discord.Embed(title="Balance Graph", color=0xFF00FF)
    embed.set_image(url=f"attachment://balanceGraph.png")

    await message.send(file=file, embed=embed)

    os.remove(f"temp/bal{userid}.png")


@bot.command(
    help = f"Guides on how to earn a currency.\nFormat: {prefix}earn <credits | unity | gems>",
    aliases = ['howtoearn', 'waystoearn'],
)
async def earn(message, currency: str): 
    currency = currency.lower()
    
    if currency in WAYS_TO_EARN:
        await message.send(embed=basicMsg(f"Ways to earn {currency.capitalize()}", WAYS_TO_EARN[currency]))
    else:
        await message.send(embed=errorMsg(f"{currency.capitalize()} is not a valid currency!\nIt must be either Credits, Unity, or Gems"))

@bot.command(
    help = f"Buy an item from the shop. Format: {prefix}buy <item id>",
    description = "Notice: For this command, item ID can contain spaces without the requirement of quotation marks.",
    aliases = ['purchase'],
)
async def buy(message, *itemID): # command is an argument    
    # Detect amount

    try:
        amt: str = itemID[-1]
        if amt.isdigit():
            amount = int(amt)
            itemID = itemID[:-1]
        else:
            amount = 1
    except IndexError:
        amount = 1

    if itemID is None: 
        await message.send(embed=errorMsg("Item ID is not specified"))
        return

    with open("shop.json", 'r') as f:
        shopitems = json.load(f)

    # Title
    itemID = str(' '.join(itemID)).title()

    if itemID not in shopitems:
        await message.send(embed=errorMsg(f"Item ID ({itemID}) is not vaild"))
    else:
        item = shopitems[itemID]
        u = User(message.author.id, doNotCheck=True) # Prevent the case of data corruption

        creds, unity, gems = u.getData("credits"), u.getData("unity"), u.getData("gems")

        # Check for balance
        if (
            (creds >= item['credits'] or item['credits'] <= 0) and
            (unity >= item['unity'] or item['unity'] <= 0) and
            (gems  >= item['gems'] or item['gems'] <= 0)
        ):
            items: list = u.getData('items')

            itemCount = items[itemID]['count'] if itemID in items else 0

            # Max limit acheived
            if itemCount >= item['limit']:
                await message.send(embed=errorMsg("Item limit reached!"))
                return
            
            # Out of stock
            if item['stock'] <= 0:
                await message.send(embed=errorMsg("Item is out of stock!"))
                return

            # Append Items
            if itemID not in items:
                items[itemID] = {
                    "expires": [],
                    "data": {},
                    "count": 0
                }

            items[itemID]['count'] += 1
            if item['expiry'] != -1:
                items[itemID]['expires'].append(int(time.time() + item['expiry']))
            else:
                items[itemID]['expires'].append(-1)

            # Remove balance
            u.addBalance(credits = -item['credits'], unity = -item['unity'], gems = -item["gems"])
            # Add item
            u.setValue("items", items)

            # Remove a stock
            shopitems[itemID]['stock'] -= 1

            with open("shop.json", 'w') as f:
                json.dump(shopitems, f, indent=4)

            await message.send(embed=successMsg(title="Item bought!", description=f"Successfully bought `{itemID}` for `{item['credits']} Credits`, `{item['unity']} Unity`, and `{item['gems']} Gems`"))

        else:
            await message.send(embed=errorMsg(f"You do not have enough currencies to buy this item!\n## Tips:{WAYS_TO_EARN['credits']}"))



@bot.command(
    help = "Start a server",
)
async def start(message, value: str): # command is an argument

    await message.send(
        requests.post("http://vm.kcservers.ca/servercmd", data=json.dumps({"user": message.author.display_name, "cmd": "start", "value": value})).text
    )



@bot.command(
    help = "View shop items",
)
async def shop(message): # command is an argument
    embed = discord.Embed(title="Shop Items", color=0xFF00FF)

    with open("shop.json", 'r') as f:
        shopitems = json.load(f)

    for i in shopitems:

        costs = []
        item = shopitems[i]
        inflation = calcInflation()
        if item['credits'] != 0: costs.append(f"{round(item['credits'] * inflation, 2)} Credits")
        if item['unity'] != 0: costs.append(f"{item['unity']} Unity")
        if item['gems'] != 0: costs.append(f"{item['gems']} Gems")

        if len(costs) > 1:
            costsTxt = ", ".join(costs[:-1]) + ", and " + costs[-1] 
        elif len(costs) == 1:
            costsTxt = costs[0]
        else:
            costsTxt = "Free"

        embed.add_field(name=f"{i} ({costsTxt})", value=item['description'] + f"\n*{('Expires after `' + time_format(item['expiry']) + '`') if item['expiry'] != -1 else 'Never expires'} | Limit: `{item['limit']}` | Stock: `{get_prefix(item['stock'], 0)}`*", inline=False)

    await message.send(embed=embed)

from games import GoFish

@bot.command(help = 'Play GoFish with the bot on difficulty 1 (less = harder)')
async def gofish(message):
    botDifficulty = 1

    u1 = User(message.author.id)
    u2 = User("bot2")
    game = GoFish(u1, u2)


    botKnowns = []

    async def bot():
        """BOT AI"""
        got = False
        # Ask a user 
        cards = game.players[u2]
        for c in cards:
            if c in botKnowns:
                if random.randint(1, botDifficulty):
                    gt = game.ask_user(u2, c)
                    if gt > 0:
                        got = True
                    botKnowns.remove(c)
                    await message.send(f"Bot turn! Bot asked {c} and got {gt} cards from you!")
                    break
        else:
            # Guess a random card
            try:
                randomC = random.choice(cards)

            except IndexError:
                game.get_from_deck(u2, random.choice(game.totalCards))
                randomC = random.choice(cards)

            gt = game.ask_user(u2, randomC)
            if gt > 0:
                got = True
            await message.send(f"Bot asked {randomC} randomly and got {gt} cards from you!")

        # Determine full cards
        d = game.determine_full_card(u2)
        if d != False:
            await message.send(f"Bot got a full deck of {d}. Current fulls: {game.playersFullCards[u2]}")

        # Continue
        if got:
            bot()

    cards = game.players[u1]


    async def determine():
        if len(game.totalCards) <= 0:
            await message.send("Game over!")
            if len(game.playersFullCards[u1]) > len(game.playersFullCards[u2]):

                # Add temporary credit gain

                credits = calcCredit(40, u1) * calcInflation()
                
                u1.addBalance(credits=credits)

                await message.send(f"Player won! You gained `{credits} credits!`")
            else:
                await message.send("Bot won!")
            return True
        else:
            return False

    #await message.send(game.players)

    while True:
        if await determine(): break

        #await message.send(game.players[u2])
        cards.sort()

        if len(cards) == 0:
            game.get_from_deck(u1, random.choice(game.totalCards))

        card = await msginput(message, f"Your turn!\nYour cards: {cards}\n\nCard to ask (input)...")


        if card.isdigit():
            card = int(card)
        elif card.lower() == "exit":
            await message.send("Exited GoFish game")
            return
        else:
            await message.send("You must provide an integer! Type exit to exit")
            continue

        if card not in cards:
            await message.send("You must choose a card from your deck!")
            continue

        # The bot sees it so append
        if card not in botKnowns: botKnowns.append(card)
        
        #game.ask_user(u1, card)
        got = game.ask_user(u1, card)
        await message.send(f"You asked {card} and got {got} cards from the bot!")

        d = game.determine_full_card(u1)
        if d != False:
            await message.send(f"You got a full deck of {d}! Current fulls: {game.playersFullCards[u1]}")

        # Continue
        if got > 0:
            continue
        
        if await determine(): break
        
        # Bot 
        await bot()
    



# ONLY FOR BETA BOT!
# So dangerous, that it can ONLY be ran on the beta bot.
    

                    
@bot.command(
    name='set',
    help = f"[DEBUG FEATURE] Sets a value for your account. Format: {prefix}set <key> <value>",
    hidden = True
)
async def setvaluecmd(message, key, value): # command is an argument
    def detect_data_type(var):
        var = str(var)
        try: 
            return json.loads(var)
        except:
            try: 
                if var.lower() == "true": return True
                elif var.lower() == "false": return False
                else: raise Exception()
            except:
                # numbers now
                if var.isdigit(): return int(var)
                else:
                    try: 
                        return float(var)
                    except:
                        return str(var)
    if bot.application_id == 1228567790525616128 or message.author.id in [1220215410658513026, 1228567790525616128]:

        u = User(message.author.id)
        v = detect_data_type(value)
        u.setValue(key, v)

        await message.send(f"Set {key} to be {v} ({type(v)})")
    else:
        await message.send(embed=errorMsg(f"You do not have permission to use this command!"))
bot.remove_command('help')
# To create a help description, add help="help description" to bot.command()
# If you do not want the command to be shown in help, add hidden = True
@bot.command(
    help = "Shows information about a bot command.",
    description = \
f"""**How to use the help command**:\nThe help command returns a list of all bot commands as well as a basic description under each command.\nThe help command can be specified with a command as an argument to obtain more details about the command.\n\n**How to read arguments**:\nEach argument that is enclosed with arrows (<>) means the argument is __mandatory__, meaning that you must specify it when running the command.\nAn argument enclosed with square brackets ([]) means that the argument is __optional__, and you do not need to specify it for the command to work properly.\nFor example, the current help command format is: `{prefix}help [command]`\nSince you specified the help command, it returned this message."""
)
async def help(message: discord.Message, command: str = "1"): # command is an argument
    embed = discord.Embed(
        title = "Help",
        color=0xFF00FF
    )
    # Due to the help command only supporting up to 25 commands, this command now splits the commands into pages that contain 10 commands each
    commandsPerPage = 10

    # This means a rewrite of the code is needed

    # If a number on command is not specified then it is probably a detailed view. In that case,
    if not str(command).isdigit():
        command = command.lstrip(prefix)
        if command in bot.all_commands:
            cmd = command
            originalcmd = str(bot.get_command(command))

            description = f"**{prefix}{originalcmd}**\n"

            cmdHelp = bot.all_commands[cmd].help
            if cmdHelp is None: 
                cmdHelp = "No basic description provided"
            
            description += cmdHelp

            if bot.all_commands[cmd].description != "":
                description += "\n\n**Description:**\n" + bot.all_commands[cmd].description
    

            # Aliases
            aliases = bot.all_commands[cmd].aliases
            # Prevent repeating
            if len(aliases) > 0: 
                description += "\n\n**Aliases: **\n" + ", ".join(prefix+i for i in aliases)

            embed.description = description

            # Reward
            u = User(message.author.id)

            data = u.getData()

            if "helpCmds" not in data:
                u.setValue("helpCmds", [])

            cmdsUsed = u.getData('helpCmds')
            if originalcmd not in cmdsUsed and not bot.get_command(command).hidden:
                cmdsUsed.append(originalcmd)
                u.setValue("helpCmds", cmdsUsed)
                u.addBalance(credits=50)
                embed.set_footer(text="+50 Credits due to viewing the details about this command for the first time!")

        else:
            embed.description = f"Command `{command}` is not a vaild command!"

        await message.send(embed=embed)
        return
    # Otherwise, it is probably a page number. Therefore...

    def get_help_commands(page: int = 1) -> discord.Embed:
        # Step 1: Obtain all commands and remove aliases and stuff
        cmds: dict[str: str] = {} 

        for cmd in bot.all_commands:
            if bot.get_command(cmd).hidden: 
                continue

            cmdHelp = bot.all_commands[cmd].help
            if cmdHelp is None: 
                cmdHelp = "No description"

            # Aliases
            aliases = bot.all_commands[cmd].aliases
            # Prevent repeating
            if cmd in aliases: continue 

            cmds[cmd] = cmdHelp

        # Sort commands by alphabetical order
        cmds = dict(sorted(cmds.items()))

        # Step 2. Determine page
        # Can be done by doing some math. Start index should be (page - 1)(commandsPerPage) and end should be (startIndex + commandsPerPage -1)

        startI = (page - 1) * commandsPerPage
        endI = (startI + commandsPerPage - 1) # -1 + 1 cancels. (see for loop) but -1 for readability

        # Step 3. Write embeds
        for i in range(startI, endI + 1):
            # If it is out of index, just exit the for loop and send the message
            try:
                cmd = list(cmds)[i]
            except IndexError: 
                break
            desc = cmds[cmd]
            embed.add_field(name = prefix + cmd, value = desc, inline=False)

        embed.set_footer(text=f"Use {prefix}help [command] to display detailed information about a command. \nThe first time you run a detailed help command about a command, you will gain 50 Credits.\nUse {prefix}help [page] to go to another page. Current page: {page}/{len(cmds) // commandsPerPage + 1}")

        return embed



    def check(reaction: discord.reaction.Reaction, user):
        return user == message.author and (str(reaction.emoji) in ('⬅️', '➡️') and reaction.message.channel == message.channel)
    
    # Step 4. Send embed to chat
    msg = await message.send(embed=get_help_commands(int(command)))




@bot.event 
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
          
        embed=discord.Embed(title="Command on cooldown!",description=f"{ctx.author.mention}, you can use the `{ctx.command}` command <t:{int(time.time() + round(error.retry_after))}:R>", color=0xff0000)
        await ctx.send(embed=embed)
    elif isinstance(error, commands.errors.MemberNotFound): #or if the command isnt found then:
        embed=discord.Embed(description=f"The member you specified is not vaild!", color=0xff0000)
        (ctx.command).reset_cooldown(ctx)
        await ctx.send(embed=embed)

    else:
        embed = discord.Embed(title='An error occurred:', colour=0xFF0000) #Red
        embed.add_field(name='Reason:', value=str(error).replace("Command raised an exception: ", '')) 
        if "KeyError" in str(error):
            if str(error).replace("Command raised an exception: ", '').replace("KeyError", "").replace("'", "") in usersFile.userTemplate:
                embed.description = "*This is most likely due to account errors.*"
        print(traceback.format_exc())
        await ctx.send(embed=embed)
        (ctx.command).reset_cooldown(ctx)


@bot.command(aliases=['reload'], hidden=True)
async def restart(ctx):
    if ctx.author.id in adminUsers:
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name="me get updated"))
        embed=discord.Embed(title=f"Restarting the program...", description=f"... is it working?", color=0x00CCFF)
        await ctx.send(embed=embed, delete_after=3.0)
        os.execl(sys.executable, sys.executable, *sys.argv)


@bot.command( hidden=True)
async def reset(message):
    if message.author.id in adminUsers:
        await message.send(f"""# A reset has been called!
If the bot is not restarted within 5 minutes, a reset will happen!
Any balances (e.g. Credits) will be lost after the reset, so please make sure to exchange them before it is too late!
-# Warning: Exchanging Credits into KCash may affect your score ranking!
<@&1328848138252980311>""")
        await asyncio.sleep(300)

        # Obtain scores
        usersDir = os.listdir('users')

        users = []
        for file in usersDir:
            if file == "main.json": continue
            u = file.replace(".json", '')
            if User(u).getData("credits") != 0: 
                users.append(u)


        scores = {}
        totalScore = 0
        for u in users:
            s = calcScore(User(u))
            scores[u] = s
            totalScore += s

        sortedScore = sorted(scores.items(), key=lambda x:x[1], reverse=True)


        avgscore = round(totalScore / len(sortedScore), 2)

        await message.send(f"""# THE BOT IS RESETTING!!!
Average Score: {avgscore}
        """)

        await asyncio.sleep(3)
        msgs = []
        for i in range(5):
            try:
                usr = sortedScore[i]
            except IndexError: 
                break

            score = usr[1]
            user = usr[0]
            with open("users/"+user+'.json', 'r') as f:
                data = json.load(f)

            msgs.append(basicMsg(
                title=f"""Place #{i+1}""",
                description = f"""
## <@{user}>
### **Total Score**: `{score}`
{calcScore(User(user), msg=True)[1]}
### Gems Gained: `{(5 - i) ** 2 * 2}`"""))
            # Add
            data['gems'] += (5 - i) ** 2 * 2
        
            with open("users/"+user+'.json', 'w') as f:
                json.dump(data, f)

        usersDir = os.listdir('users')

        for user in usersDir:
            with open(os.path.join('users', user), 'r') as f:
                data = json.load(f)

            try:
                os.remove(os.path.join("balanceLogs", user.replace('.json', '')))
            except FileNotFoundError:
                pass

            data['credits'] = 500
            data['unity'] = 20

            data['items'] = {"Prosperous Reset": {"expires": [int(time.time() + 60*60*24*3)], "data": {}, "count": 1}}
            data['job'] = None
            data['bs%'] = 0
            data['helpCmds'] = []
            data['log'] = 0
            data['rob'] = {
                "atk": 5,
                "def": 5, 
                "insights": 0,
                "won/lost": [0, 0],
                "attackedTime": 0,
                "attackTime": 0,
            }
            if 'players' in data:
                del data['players']

            with open(os.path.join('users', user), 'w') as f:
                json.dump(data, f)

        # Main bot
        with open("users/main.json", 'r') as f:
            data = json.load(f)

        data['credits'] = 50000
        data['unity'] = 0
        data['items'] = {"Precognition": {"expires": [-1], "data": {}, "count": 1}, "Lock": {"expires": [-1, -1, -1, -1, -1], "data": {}, "count": 5}}
        data['job'] = 'Player'
        data['bs%'] = 100
        data['helpCmds'] = []
        data['log'] = 0
        data['rob'] = {
            "atk": 0,
            "def": 10, 
            "insights": 0,
            "won/lost": [0, 0],
            "attackedTime": 0,
            "attackTime": 0,
        }
        if 'players' in data:
            del data['players']

        with open("users/main.json", 'w') as f:
            json.dump(data, f)

        # Send msgs
        for msg in msgs:
            await message.send(embed=msg)
            await asyncio.sleep(5)

        await message.send("# THE BOT HAS BEEN RESETTED!\nCongratulations to the top 5 members of this reset!")

def predict_discord_status(userID: int, hour_of_day, minute_of_hour, day_of_week) -> tuple[bool, float]:
    """Predict when someone will be online. """
    with open(r"C:\Users\minec\Desktop\MENU\Programs\Python\KCServers Bot Testing\KCServersBot\userschedules.json", 'r') as f:
        data = json.load(f)[str(userID)]

    print('data ', data)
    # Convert to a DataFrame
    df = pd.DataFrame(data)

    # Feature matrix X (hour_of_day, minute_of_hour, day_of_week)
    X = df[['day', 'hr', 'min']]

    # Target variable y (is_online)
    y = df['status']

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Initialize and train a Random Forest Classifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Predict on the test set
    y_pred = model.predict(X_test)

    # Evaluate the model
    accuracy = accuracy_score(y_test, y_pred)
    

    # Predict if you'll be online or offline at a given time
    def predict_availability(hour_of_day, minute_of_hour, day_of_week):
        # prediction = model.predict([[day_of_week, hour_of_day, minute_of_hour]])[0]

        input_data = pd.DataFrame([[day_of_week, hour_of_day, minute_of_hour]], columns=['day', 'hr', 'min'])
    
        # Predict and return result
        prediction = model.predict(input_data)[0]
        
        return ('Online', accuracy) if prediction == 1 else ('Offline', accuracy)
    
    return predict_availability(hour_of_day, minute_of_hour, day_of_week) 

@bot.command(hidden=True)
async def predictstatus(message, member: discord.Member, t: str):
    # Define the MST timezone
    mst_timezone = pytz.timezone('US/Mountain')

    # Get the current time in UTC
    utc_now = datetime.datetime.now(pytz.utc)

    # Convert the current time to MST
    mst_now = utc_now.astimezone(mst_timezone)

    # Extract hour, minute, and day of the week
    hour_of_day = mst_now.hour
    minute_of_hour = mst_now.minute
    day_of_week = mst_now.weekday()  # 0 = Monday, 6 = Sunday

    try:
        day, hr, min = t.split(":")
    except (ValueError, KeyError):
        try:
            day = day_of_week
            hr, min = t.split(":")
        except (ValueError, KeyError):
            min = 0
            hr = t

    day = int(day)
    hr = int(hr)
    min = int(min)

    wkconv = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }
    await message.send(f"{day} {hr} {min}")

    status, acc = predict_discord_status(str(member.id), hr, min, day)

    await message.send(embed=basicMsg("Status Prediction", description=f"""During {hr}:{min} on {wkconv[day]}s, {member.mention} will be **{"online" if status else "offline"}**\nAccuracy: {round(acc * 100, 2)}%"""))
# Run the bot based on the token in the .env file
bot.run(os.getenv("DISCORD_TOKEN"))
