"""
PIP REQUIREMENTS:
pip install requests mcstatus discord.py names matplotlib scipy
"""
import discord, json, random, time, traceback, names, re, datetime
from discord.ext import commands, tasks
import time, os, sys, threading, dns, requests, asyncio, math
import dns.resolver
from mcstatus import JavaServer
from users import User
import users as usersFile
from games import CrashGame, Players
import games
from traceback import print_exc as printError
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

from calculatefuncs import *

usersFile.botID = "1220215410658513026"

KMCExtractLocation = "\\\\KCHOSTINGPC\\Desktop\\MENU\\ServerStuff\\!KMCExtract"

with open("botsettings.json", 'r') as f:
    data = json.load(f)

    prefix = data['prefix']
    TOKEN = data['token']
    inflationAmt = data['inflation amount']

activity = discord.Activity(type=discord.ActivityType.watching, name=f"KCMC Servers (V.3.0)")
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




def robCalc(user: User, percentage = 5):
    winAmount = int(percentage) / 100

    amounts = {}
    winAmounts = {}

    for target in bot.get_all_members():
        
        if str(target.id) == str(user.ID) or (user.ID == "main" and (str(target.id) == str(bot.user.id))): continue

        targetUser = User(target.id)

        # Amounts
        lostAmount = round(targetUser.getData('credits') / 20 + user.getData('credits') / 10, 2)
        winAmounts[lostAmount] = round(targetUser.getData('credits')/10, 2)

        amounts[lostAmount] = target.id

    reversedWinAmounts = {v: k for k, v in winAmounts.items()}

    sortedAmounts = {}
    for i in sorted(list(amounts)):
        sortedAmounts[i] = amounts[i]
    
    sortedReversed = sorted(list(reversedWinAmounts), reverse=True)

    mostGainedLostAMT = reversedWinAmounts[sortedReversed[0]]
    mostGained = amounts[mostGainedLostAMT]

    allMembers = "\n".join(f"<@{amounts[i]}>: {i} lost, {winAmounts[i]} won" for i in sortedAmounts)
    embed = discord.Embed(title="Best person to rob", description=f"""The least costly person to rob is <@{amounts[list(sortedAmounts)[0]]}> ({list(sortedAmounts)[0]}).\nThe most gained when robbing is <@{mostGained}> ({sortedReversed[0]}).\n\n**Values:**\n{allMembers}""")
    
    return amounts[list(sortedAmounts)[0]], sortedReversed[0]
    
previousba = 0


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
    
        
    channel = bot.get_channel(1241127368916209664)

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

    async def rob():
        try:
            
            bestrob, mostrob = robCalc(u)
            if credits * 2 >= get_user(bestrob).get("credits") * 0.05:
                await run('rob', target=bot.get_user(int(bestrob)))

        except: printError()

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

    embed.description = json.dumps(userData)

    await message.send(embed=embed)


@bot.command(
    help = "Displays account stats",
    aliases = ["pf", "profile", "acc", "balance", "bal"]
)
async def account(message, account: discord.Member = None, usejson: str = "false"):
    embed = discord.Embed(
        title = "Account information",
        color = 0xFF00FF
    )
    if account is None:
        account = message.author

    user = User(account.id)

    userData = user.getData()
    
    if usejson.lower().startswith('t') or usejson.lower().startswith('j'):
        await message.send(json.dumps(userData))
        return

    ign = str(userData['IGN'])#.replace('_', '\\_')

    try:
        with open('pingservers.json', 'r') as f:
            kcashEarningServ = json.load(f)[str(account.id)]
    except:
        kcashEarningServ = "None"

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
        value=f"**Credits**: `{numStr(userData['credits'])}`\n**Unity**: `{numStr(userData['unity'])}/200`\n**Gems**: `{numStr(userData['gems'])}`"
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
    # Get count of itms
    itemCount = {}
    for i in userData['items']:
        item = i['item']
        if item not in itemCount:
            itemCount[item] = 1
        else:
            itemCount[item] += 1

    itemsPresent = []
    for item in userData['items']:
        if item['item'] not in itemsPresent:
            itemsTxt.append(
                f"**{item['item']}** ({itemCount[item['item']]}/{shopitems[item['item']]['limit']})" + ": " + 
                (f"Expires <t:{round(item['expires'])}:R>" if item['expires'] != -1 else "Never expires")
            )
            itemsPresent.append(item['item'])

    embed.add_field(
        name=f"Items", 
        value="\n".join(itemsTxt if itemsTxt != [] else ["No items"]),
        inline=False
    )
    embed.add_field(
        name="Other Info", 
        value=f"**Wealth Power**: `{calcWealthPower(user)}%`\n**Bot Stock%**: `{userData['bs%']}`",
        inline=False
    )

    msg = await message.send(embed=embed)


    # Get KCash - offline until a server/API is made
    kcash = "Offline"

    embed.set_field_at(
        index = 1,
        name="KCMC Info", 
        value=f"**MC Username**: `{ign}`\n**KCash**: `{kcash}`"
    )    
    # embed.set_field_at(
    #     index = 5,
    #     name="Other Info", 
    #     value=f"**Wealth Power**: `{calcWealthPower(user)}%`\n**bs%**: `{userData['BS%']}`",
    #     inline=False
    # )

    # Add KCash notice
    embed.set_footer(text="A new global KCash server will be up later.")

    await msg.edit(embed=embed)

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
                c = float(json.load(f)['credits'])
                if c != 0: users[file.replace(".json", '')] = c
            except: pass
    totalCredits = 0

    sortedUsers = sorted(users.items(), key=lambda x:x[1], reverse=True)
    # [("209348023", 1231)]
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

    embed.description = f"**Total Credits**: `{numStr(totalCredits)}`\n**Inflation**: `{round(inflationLvl)}%`\n**Average Credits**: `{numStr(avgcredits)}`"

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
    else:
        ign = ign.replace("\\", "")
        if user.setValue('IGN', ign):
            embed = discord.Embed(title="Success",description=f"Your Minecraft username is now set to `{ign}`", color=0x00FF00)
        else:
            embed = discord.Embed(title="Failed",description=f"An unknown error occurred while trying to set your MC username", color=0xFF0000)

    await message.send(embed=embed)



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
    description = """The daily reward gives an amount of Credits and Unity based on wealth power.\nThe command be ran every 12 hours"""
)
async def daily(message):
    user = User(message.author.id)
    data = user.getData()
    if time.time() - data["dailyTime"] < 60*60*12:
        embed = discord.Embed(title="On Cooldown!",description=f"You can claim the daily reward <t:{int(data['dailyTime'] + 60*60*12)}:R>", color=0xFF0000)
        await message.send(embed=embed)
        return


    amount = round(50 / (1 + calcWealthPower(user)/100), 2)
    unityAmt = round(5 / (1 + calcWealthPower(user)/100), 2)


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
        embed = discord.Embed(title="Daily failure",description=f"Where does the daily money come from?\nWhen you run the daily command, you actually take money away from the bot. Credits do not get created typically unless it is from the bot itself; you take the bot's money instead\nToday, the bot has decided to **rob** you instead of letting you steal it, making you lose `{numStr(50 * (1 + calcWealthPower(user)/100))} Credits` but gain `{numStr(unityAmt * 3 + 1)} Unity`.\nThe daily CD is also increased by 10%", color=0xFF0000)
        user.addBalance(
            credits=-round(50 * (1 + calcWealthPower(user)/100), 2),
            unity=unityAmt*3 + 1
        )


    await message.send(embed=embed)



@bot.command(
    help = f"Converts a currency into another",
    description = f"""Conversion rates can be found by running the command by itself.\nFormat of command: `{prefix}`""",
    aliases = ["convert", "change"],
    hidden = True
)
async def exchange(message, fromCurrency = None, toCurrency = None, amount = 0):
    user = User(message.author.id)
    data = user.getData()
    inflation = calcInflation()
    exchangeRates = {
#("credits", "unity"): round(0.1 / inflation, 4),
        #("unity", "credits"): round(4 * (inflation ** 0.75)),
    }
    exchangeFee = (0, 5)

    if fromCurrency is None:
        exchangeRateTxt = "\n".join(f"1 {f} > {exchangeRates[(f,t)]} {t}" for f, t in exchangeRates)
        embed = discord.Embed(title="Exchange information", description=f"""Format: `{prefix}exchange [from currency] <to currency> <amount of from currency to exchange>`\n*KCash exchange will be available periodically. Currently, it would be `1 Credit` > `{round(0.1 / inflation, 2)} KCash`*\n\n**Exchange fee**: `{exchangeFee[0]} Credits` and `{exchangeFee[1]} Unity` per exchange.\n**Exchange rates**:\n{exchangeRateTxt}""", color=0xFF00FF)

    elif fromCurrency not in ['gems']:
        embed = discord.Embed(title="Not a valid exchange currency!",description=f"Your exchange from currency is not valid! Valid options are credits and unity.", color=0xFF0000)
        
    elif toCurrency not in ['credits','unity']:
        embed = discord.Embed(title="Not a valid exchange currency!",description=f"Your exchange from currency is not valid! Valid options are credits and unity.", color=0xFF0000)
    elif not str(amount).isnumeric() or int(amount) <= 0:
        embed = discord.Embed(title="Amount invaild!",description=f"Your amount must be an integer greater than 0!", color=0xFF0000)
    else:
    
        for f, t in exchangeRates:
            if f == fromCurrency and t == toCurrency:
                exchangeRate = exchangeRates[(f,t)]
                if data[f] < amount:
                    embed = discord.Embed(title="Not enough currency!",description=f"Your {f.capitalize()} amount is less than the requested exchange amount which requires {amount}!", color=0xFF0000)
                else:
                    getAmount = round(amount * exchangeRate, 5)

                    if t != "kcash":
                        if f == "credits":
                            user.addBalance(credits = -amount, unity = getAmount)
                        else:
                            user.addBalance(unity = -amount, credits = getAmount)

                        # Exchange fee
                        user.addBalance(credits = -exchangeFee[0], unity = -exchangeFee[1])

                        embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} {f.capitalize()}` to `{getAmount} {t.capitalize()}`\nExchange fee: `{exchangeFee[0]} Credits`, `{exchangeFee[1]} Unity`", color=0x00FF00)
                    else:
                        # NETWORK FETCHES
                        try:
                            with open(KMCExtractLocation + "\\users.json", 'r') as file:
                                kmceusers = json.load(file)

                            getAmount = round(amount * exchangeRate, 2)
                            kmceusers[data['IGN']]['KCash'] += getAmount

                            with open(KMCExtractLocation + "\\users.json", 'w') as file:
                                kmceusers = json.dump(kmceusers, file)       
                            user.addBalance(credits = -amount)
 
                            # Exchange fee
                            user.addBalance(credits = exchangeFee[0], unity = exchangeFee[1])


                            embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} {f.capitalize()}` to `{getAmount} KCash`.\nExchange fee: `{exchangeFee[0]} Credits`, `{exchangeFee[1]} Unity`", color=0x00FF00)

                        except KeyError:
                            embed = discord.Embed(title="Not registered!",description=f"Your MC Username (`{data['IGN']}`) is not registered on KMCExtract!", color=0xFF0000)
                break

        else:
            embed = discord.Embed(title="Not a valid exchange currency!",description=f"Your exchange currencies is not valid! Run `{prefix}exchange` to see the details.", color=0xFF0000)


    await message.send(embed=embed)




# @bot.command(
#     name = "test", 
#     help = f"Yes",
#     hidden = True
# )
# async def test_cmd(message):
#     file: discord.File = await message.message.attachments[0].save("temp/tessocr.png")
#     import pytesseract
#     pytesseract.pytesseract.tesseract_cmd = r"E:\Programs\Tesseract\tesseract.exe"
#     text = pytesseract.image_to_string('temp/tessocr.png',config='--psm 6')
#     await message.send(text)


@bot.command(
    help = f"Converts gems into another currency. Run the command by itself for more info.",
    description = f"""Conversion rates can be found by running the command by itself.\nFormat of command: `{prefix} [currency <amount>]`""",
    aliases = ["ge", "gemconvert"]
)
async def gemexchange(message, currency = None, amount = 0):
    user = User(message.author.id)
    data = user.getData()
    
    exchangeRates = {
        ("gems", "unity"): 5,
        ("gems", "credits"): round(500 * calcInflation()),
    }

    if currency is None:
        exchangeRateTxt = "\n".join(f"1 {f} > {exchangeRates[(f,t)]} {t}" for f, t in exchangeRates)
        embed = discord.Embed(title="Exchange information", description=f"""Format: `{prefix}exchange [from currency] <to currency> <amount of from currency to exchange>`\n*KCash exchange will be available periodically. It is `1 Credit` > `0.1 KCash`*\n\n**Exchange rates**:\n{exchangeRateTxt}""", color=0xFF00FF)

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
    help = "Rob Calculator",
    aliases = ['calcrob', 'bestrob']
)
async def robcalc(message, percentage="5"):
    user = User(message.author.id)
    winAmount = int(percentage) / 100

    amounts = {}
    winAmounts = {}

    for target in bot.get_all_members():
        
        if target == message.author: continue

        targetUser = User(target.id)

        lostAmount = round(targetUser.getData('credits') / 20 + user.getData('credits') / 10, 2)
        winAmounts[lostAmount] = round(targetUser.getData('credits')/10, 2)
    
        amounts[lostAmount] = target.id

        winAmounts[lostAmount] = round(targetUser.getData()['credits'] * winAmount, 2)

    reversedWinAmounts = {v: k for k, v in winAmounts.items()}

    sortedAmounts = {}
    for i in sorted(list(amounts)):
        sortedAmounts[i] = amounts[i]
    
    sortedReversed = sorted(list(reversedWinAmounts), reverse=True)

    mostGainedLostAMT = reversedWinAmounts[sortedReversed[0]]
    mostGained = amounts[mostGainedLostAMT]

    allMembers = "\n".join(f"<@{amounts[i]}>: {i} lost, {winAmounts[i]} won" for i in sortedAmounts)
    embed = discord.Embed(title="Best person to rob", description=f"""The least costly person to rob is <@{amounts[list(sortedAmounts)[0]]}> ({list(sortedAmounts)[0]}).\nThe most gained when robbing is <@{mostGained}> ({sortedReversed[0]}).\n\n**Values:**\n{allMembers}""")
    
    await message.send(embed=embed)

    # For AI
    return (amounts[list(sortedAmounts)[0]], amounts[i])

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

While robbing, the difference between the amount of money you have increases the target's Rob Defenses by a certain amount. 
The equation of this additional Defense gain is modelled by the equation: *`log(|(Your Balance) - (Target Balance)| + 1) ^ 2`*

Also when failing a rob, you gain an *Insight*, increasing your chances of suceeding at the cost of your rob defenses decreasing.
Insights can stack up to 3 times and reset when succeeding a rob or being successfully robbed by another.

Additional factors:
* Target is offline or idle: Target Defense Rob -1
* Already robbed that target within 5 minutes: Target Defense Rob +1
* Has an Insight: Rob Attack +1 but Rob Defense -1 (Stacks up to 3 times)
target
Essentially, it is way easier for the target to gain Rob Defenses than it is for you to gain Rob Attacks, making it harder for you to successfully rob someone.

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
async def rob(message, target: discord.Member):
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
        embed = discord.Embed(title="An error occurred!",description=f"Cannot rob yourself!\n*imagine being mj lol*", color=0xFF0000)
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
    diffRDL = int(math.log10(abs(userBal - targetBal) + 1) ** 2)
    targetRDL += diffRDL

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

    # Attacked times
    robSet(user, "attackTime", int(time.time()))
    robSet(targetUser, "attackedTime", int(time.time()))

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

            # Lose money
            user.addBalance(credits = -loseAmount)
            targetUser.addBalance(credits = loseAmount)

            # Rob stats
            if robGet(user, 'insights') < 3:
                robAdd(user, "insights", 1)

            wl = robGet(user, "won/lost")
            robSet(user, "won/lost", [wl[0], wl[1]+1])


        em = discord.Embed(
            title = "Rob Results",
            description = f"""Robbing {target.mention}...

**Your Roll**: `{userRoll}`
**{target.mention}'s Roll**: `{targetRoll}`

**{winTxt}**""",
            color = 0xFF00FF,
        )
        if diffRDL > 0:
            em.set_footer(text = f"Target obtained +{diffRDL} Rob Defense due to differences in Credit balance")

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
            (f"\n  `{'+' if gems > 0 else ''}{gems} Credits`" if gems != 0 else "")
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

    if message.author.id in [623339767756750849]:
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
async def stockold(message, server=None):

    """
    stock {
        stockpct: float
        initbal: float
        inittime: time.time()
    }
    """
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
    description = """""",
    aliases = ['job'],
    hidden = True
)
async def work(message, cmd = None, value = None):
    user = User(message.author.id)
    data = user.getData()

    JOBS = {
        "Software Developer": {
            "description": "A developer working in KCServers. Solve 'easy' programming problems (Python for code) to earn money",
            "work output": 25,
            "credit perk": -5
        },
        # "Police": {
        #     "description": "A policeman, catching thiefs. They have increased chances of robbers failing.",
        #     "work output": 5,
        #     "credit perk": -5
        # },
        # "Robber": {
        #     "description": "A thief. They have increased chances of successful robs",
        #     "work output": 5,
        #     "credit perk": -5
        # },
        "Math": {
            "description": "i need practice on quadratics lol",
            "work output": 50,
            "credit perk": -10
        },
        # "Gamer": {
        #     "description": f"A KCMC gamer. The KCash earned from `{prefix}setserver` every minute increases by 0.5",
        #     "work output": 0,
        #     "credit perk": 0
        # },
        # "Nurse": {
        #     "description": f"A nurse job. The Unity gained from `{prefix}daily` increases by 3",
        #     "work output": 100,
        #     "credit perk": -15
        # },
        # "Researcher": {
        #     "description": f"A researcher. The Unity gained from `{prefix}daily` increases by 3",
        #     "work output": -50,
        #     "credit perk": 10
        # }
    }

    if cmd is None:

        embed = discord.Embed(
            title="Work jobs",
            description=(
                f"Apply using `{prefix}work apply <job>`\n"
                "Work output is an additional money gain from work.\n"
                "\n**Jobs:**\n" + 
                "\n".join(f"""**{job}**: {JOBS[job]['description']}\nPerks: `{"+" + str(JOBS[job]['work output']) if JOBS[job]['work output'] >= 0 else JOBS[job]['work output']}% work output`, `{"+" + str(JOBS[job]['credit perk']) if JOBS[job]['credit perk'] >= 0 else JOBS[job]['credit perk']}% Credit earnings`""" for job in JOBS)
            ), 
            color=0xFF00FF
        )
        await message.send(embed=embed)
        return



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
        if message.author.display_icon is not None:
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_icon)
        else:
            embed.set_author(name=message.author.display_name, icon_url="https://kevcoremc.github.io/purpletransparentKC.png")

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
    await message.send("Sorry, but until there are more questions in the bank, I am disabling this command lol good luck with your unity problems")
    return

    u = User(message.author.id)

    # if message.author.id not in [989387917111721995, 623339767756750849, 639206421707227136, 695703574465740851, 889635268070629436]:
    #     await message.send(embed=errorMsg("You are not whitelisted to use this command!\nCheck out this command in the official bot later (V.2.2)"))
    #     return

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
     
@bot.command(
    help = f"Play a simliar version of Hangman",
    description = """A random word will be chosen from a bank. You will have letter attempts and guess attempts. Say a letter to guess a letter, and anything else to guess the word. It costs `8 Credits` to play the game though negative balances are still allowed..""",
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
        title = "Minecraft Item Guessing Game",
        description = f"""A random word was chosen from a bank. Say a letter to guess a letter. Type the full word to win.
At anytime in the game, type `exit` to exit out of the game.
Winning will give you `{cred()} Credits`.

**`{' '.join(i for i in scrambled)}`**

Attempts left: `{attempts}`
Word Guesses left: `{guesses}`

Guessed: `{', '.join(guessed if len(guessed) > 0 else (' ',))}`
*There is {len(items)} items that the game can choose from*
        """,
        color=0xFF00FF

    ))

    async def edit(text: str):
        await msg.edit(embed=discord.Embed(
            title = "Minecraft Item Guessing Game",
            description = f"""A random word was chosen from a bank. Say a letter to guess a letter. Type the full word to win.
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
    description = """In order to perform a graphing operation, the bot reads the last 1000 lines of the balance log files. This means that an active balance change from other users may make the graph detect nothing""",
    aliases = ['gb', 'graphbal', 'balgraph', 'bg', 'balancegraph']
)
@commands.cooldown(3, 10, commands.BucketType.user) 
async def graphbalance(message: discord.Message, user: discord.Member = None, *, timeframe: str = "1d"):
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


    # Initialize a list to store the balances
    balances = []
    xstrs = []

    with open(os.path.join("balanceLogs", str(userid)), 'rb') as f:
        # Move the pointer to the end of the file
        f.seek(0, 2)
        # Get the file size
        size = f.tell()

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

    # If there is only 1 item in the list, nothing will be graphed, so add the same value to the balance.
    if len(balances) == 1:
        balances = balances * 2

    balances.reverse()

    xvalues = [i for i in range(len(balances))]

    xstrs.reverse()

    # Create plot

    plt.xlabel(f"Timeframe ({tf})")
    plt.ylabel("Credit Balance")

    # If too much data then don't show on graph
    if len(xstrs) < 30:
        plt.xticks(xvalues, xstrs)
        tf = "Indexes"

    plt.title(f"{user.display_name}'s balance changes since {human_time_duration(total)} ago")

    # try:
    #     idx = range(len(xvalues))
    #     xnew = np.linspace(min(idx), max(idx), 300)

    #     # interpolation
    #     spl = make_interp_spline(idx, balances, k=2)
    #     smooth = spl(xnew)

    #     # plotting, and tick replacement
    #     plt.plot(xnew, smooth, "b")
    # except ValueError:

    # Slope color
    try:
        first, last = balances[0], balances[-1]
        if first > last: color = 'red'
        elif first < last: color = 'green'
        else: color = 'gray'
    except IndexError:
        color = 'gray'

    plt.plot(xvalues, balances, color=color)

#    plt.plot(xvalues, balances)

    plt.savefig(f"temp/bal{userid}.png")
    plt.clf()

    file = discord.File(f"temp/bal{userid}.png", filename=f"balanceGraph.png")
    embed = discord.Embed(title="Balance Graph", color=0xFF00FF)
    embed.set_image(url=f"attachment://balanceGraph.png")

    await message.send(file=file, embed=embed)

    os.remove(f"temp/bal{userid}.png")


@bot.command(
    help = f"Buy an item from the shop. Format: {prefix}buy <item id>",
    description = "Notice: For this command, item ID can contain spaces without the requirement of quotation marks.",
    aliases = ['purchase'],
)
async def buy(message, *itemID): # command is an argument    
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
            creds >= item['credits'] and
            unity >= item['unity'] and
            gems  >= item['gems']
        ):
            items: list = u.getData('items')

            itemPresent, itemCount = getItem(u, itemID, count = True)
            # Max limit acheived
            if itemCount >= item['limit']:
                await message.send(embed=errorMsg("Item limit reached!"))
                return
            
            # Out of stock
            if item['stock'] <= 0:
                await message.send(embed=errorMsg("Item is out of stock!"))
                return

            items.append({
                "item": itemID, 
                "expires": (time.time() + item['expiry']) if item['expiry'] != -1 else -1,
                "data": {}
            })


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
            await message.send(embed=errorMsg(f"You do not have enough currencies to buy this item!"))



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

@bot.command(help = 'Play GoFish with the bot on difficulty 3 (less = harder)')
async def gofish(message):
    botDifficulty = 3

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
                    await message.send(f"Bot asked {c} and got {gt} cards from you!")
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
                await message.send("Player won!")
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


        await message.send(f"\nYour turn!\nYour cards: {cards}")

        card = await msginput(message, f"Card to ask (input)...")


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
        await message.send("Bot turn!")
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

        embed.set_footer(text=f"Use {prefix}help [command] to display detailed information about a command. \nThe first time you run a detailed help command about a command, you will gain 50 Credits.\nUse {prefix}help [page] to go to another page. Current page: {page}/{len(cmds) // commandsPerPage}")

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
        embed.set_footer(text=f"Debug notes: ln {traceback.extract_stack()[-1][1]}")
        await ctx.send(embed=embed)
        (ctx.command).reset_cooldown(ctx)



@bot.command(aliases=['reload'], hidden=True)
async def restart(ctx, arg1=None):
 
    if ctx.author.id == 623339767756750849:

        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name="me get updated"))
        if arg1 == "update":
            embed=discord.Embed(title=f"Restarting the program...", description=f"and git pulling as well...", color=0x00CCFF)
            await ctx.send(embed=embed, delete_after=3.0)
            os.system('git pull')
            time.sleep(3)
        else:
            embed=discord.Embed(title=f"Restarting the program...", description=f"... is it working?", color=0x00CCFF)
            await ctx.send(embed=embed, delete_after=3.0)
        os.execl(sys.executable, sys.executable, *sys.argv)



bot.run(TOKEN)
