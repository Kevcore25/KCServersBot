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
from traceback import print_exc as printError
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from dotenv import load_dotenv
from calculatefuncs import *
import cmds

print("Finished importing")
load_dotenv()



with open("botsettings.json", 'r') as f:
    botsettings = json.load(f)

    KMCExtractLocation = botsettings['KMCExtract']
    prefix = botsettings['prefix']
    inflationAmt = botsettings['inflation amount']
    adminUsers = botsettings['admins']
    botAIChannel = botsettings['AI Channel']
    serverID = botsettings['Server ID']

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
    # t = &ba.Timer(60, kcashEarningLoop)
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
    print("Ready!")

    statusloop()

    print("Registering commands...")
    # ADD CMDS
    await bot.add_cog(cmds.AccountViewers(bot))
    await bot.add_cog(cmds.AccountUtils(bot))
    await bot.add_cog(cmds.AdminCmds(bot))
    await bot.add_cog(cmds.BalanceGraphs(bot))
    await bot.add_cog(cmds.Exchanges(bot))
    await bot.add_cog(cmds.GambleGames(bot))
    await bot.add_cog(cmds.Informations(bot))
    await bot.add_cog(cmds.LeaderboardCog(bot))
    await bot.add_cog(cmds.TimeIncomes(bot))
    await bot.add_cog(cmds.InteractionGames(bot))

    print("Starting loops!")
    # Start Loops
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

async def msginput(ctx: discord.Message, text: str | None, timeout: int = 60) -> str:
    if text is not None: await ctx.send(text)
    ui = await bot.wait_for("message", check=lambda msg: msg.author == ctx.author, timeout=timeout)
    return str(ui.content)




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
