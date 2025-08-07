"""Calculation functions"""

from users import User
import discord, os, json, time, random
import discord.ext.commands

with open("botsettings.json", 'r') as f:
    botsettings = json.load(f)

    KMCExtractLocation = botsettings['KMCExtract']
    prefix = botsettings['prefix']
    inflationAmt = botsettings['inflation amount']
    adminUsers = botsettings['admins']
    botAIChannel = botsettings['AI Channel']
    serverID = botsettings['Server ID']

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

# Aliases
false = False
true = True

# Source : chatgpt lol stackoverflow is UESLSES
def tail(filename, lines=100) -> list[str]:
    with open(filename, 'rb') as f:
        # Move the pointer to the end of the file
        f.seek(0, 2)
        # Get the file size
        size = f.tell()
        # Initialize a list to store the last `lines` lines
        lines_list = []
        # Initialize a variable to count the number of lines read
        read_lines = 0
        # Start from the end of the file
        for i in range(size - 1, -1, -1):
            f.seek(i)
            # Read a byte
            char = f.read(1)
            # If it's a newline character and we haven't reached the end of file
            if char == b'\n' and i < size - 1:
                # Add the line to the list
                lines_list.append(f.readline().decode().rstrip())
                # Increase the count of lines read
                read_lines += 1
                # If we have read the desired number of lines, break the loop
                if read_lines == lines:
                    break
        # Reverse the list to get the lines in the correct order
        lines_list.reverse()
        return lines_list

def basicMsg(title = "Information", description = "No information provided"):
    return discord.Embed(title=title, description=description, color=0xFF00FF)

def successMsg(title = "Success", description = "The command is successful"):
    return discord.Embed(title=title, description=description, color=0x00FF00)

def errorMsg(description = "Unknown error", cause = None, title = "An error occurred"):
    c = '\n\n**Cause:** ' + str(cause) if cause is not None else ''
    return discord.Embed(title=title, description=f"{description}{c}", color=0xFF0000)

def get_prefix(value: float, accuracy: int = 0, symbol: str = "") -> str:
    """Returns a number with a shortened prefix, like 125356 into 125.3K"""
    # value = val
    # if round(value / 1000000000, accuracy) > 0:
    #     newValue = str(round(value / 1000000000, accuracy)) + "T"
    # elif round(value / 1000000, accuracy) > 0:
    #     newValue = str(round(value / 1000000, accuracy)) + "M"
    # elif round(value / 1000, accuracy) > 0:
    #     newValue = str(round(value / 1000, accuracy)) + "K"
    # else: 
    #     newValue = str(round(value, accuracy))
    
    # return newValue.replace('.0','') if accuracy == 0 else newValue

    val = abs(value)

    if val >= 1_000_000_000_000:  # Really?
        val = str(int(val / 1000000000000 * (10 ** accuracy)) / (10 ** accuracy)) + "T"
    elif val >= 1_000_000_000:
        val = str(int(val / 1000000000 * (10 ** accuracy)) / (10 ** accuracy)) + "G"
    elif val >= 1_000_000:
        val = str(int(val / 1000000 * (10 ** accuracy)) / (10 ** accuracy)) + "M"
    elif val >= 1_000:
        val = str(int(val / 1000 * (10 ** accuracy)) / (10 ** accuracy)) + "K"
    else:
        val = str(int(val))

    if accuracy == 0 and not val.isdigit():
        val = str(int(float(val[:-1]))) + val[-1]

    return ("-" + val + symbol) if value < 0 else (val + symbol)

def time_format(seconds: int) -> str:
    if str(seconds).isdigit():
        seconds = int(seconds)
        d = seconds // (3600 * 24)
        h = seconds // 3600 % 24
        m = seconds % 3600 // 60
        s = seconds % 3600 % 60
        temp = []
        if d > 0:
            temp.append(f'{d}d')
        if h > 0:
            temp.append(f'{h}h')
        if m > 0:
            temp.append(f'{m}m')
        if s > 0:
            temp.append(f'{s}s')
        return ' '.join(temp)
    else:
        return '-'


def calcInflation() -> float:
    usersDir = os.listdir('users')

    totalCredits, amtOfUsers = 0 ,0
    for file in usersDir:
        with open('users/' + file, 'r') as f:
            try:
                if file == "main.json": continue

                credits = float(json.load(f).get('credits'))
                if credits != 0: 
                    totalCredits += credits
                    amtOfUsers += 1
            except: pass

    # Inflation % = Total Credits of Members / (Inflation amount * Amount of Members) x 100 (%)
    inflationLvl = totalCredits / (inflationAmt * amtOfUsers)
    if inflationLvl < 1: inflationLvl = 1
    return inflationLvl


def calcWealthPower(u: User, decimal = False, noperks = False) -> int | float:
    """
    Calculates wealth power and returns a percentage.
    Wealth power is a measurement of wealth compared to other users.
    Users with negative or zero balances are not considered. 
    """
    # Relative Power of Credits = (Credits ) / (Average Credits of Members)  

    usersDir = os.listdir('users')

    totalWealth, amtOfUsers = 0 ,0
    botCred = User("main").getData("credits")
    for file in usersDir:
        # Do not count bot in wealth power
        if file == "main.json": continue

        try:
            userWealth = calcWealth(User(file.replace(".json", "")), botCred)
            if userWealth > 0:
                totalWealth += userWealth
                amtOfUsers += 1
        except: pass

    try:
        wealth = calcWealth(u, botCred)
        wealthpower = (wealth) / ((totalWealth - wealth) / (amtOfUsers)) * 100
    except ZeroDivisionError:
        # This edge case means the user "owns" the economy
        wealthpower = 100

    if not noperks:
        # Pacifist job (50% less multiplative)
        if u.getData('job') == "Pacifist":
            wealthpower /= 2

    # Credit power should be at a minimum of 0% (Updated from -50%)
    # Otherwise, a bug would occur where users get negative credits due to commands having a (1 + Wealth Power%) multiplication. 
    if wealthpower < 0:
        wealthpower = 0

    return round(1 + wealthpower/100, 2) if decimal else round(wealthpower) 

def calcWPAmount(u: User, amount: float, generation: int = 2, acc: int = 3) -> float:
    """
    Calculates the amount a user earns based on their wealth power.

    In gen 1, it is simply a division statement
        `Amount / (1 + Wealth Power)`

    In gen 2, it is gen 1 with wealth power being subtracted by 1, unless WP is under 1, in which WP is set to 1
    It is useful to not have a lot of Credit difference (e.g. 10 credits turns into 5 for gen 1) and also helps prevent gaining a lot from 0 Credits
        `Amount / (Wealth Power), Wealth Power > 1`

    In gen 3, it uses Work command scaling, where WP does not affect a lot.
    Every 20% WP after 100% causes earnings to reduce by 1%, up to -50% earnings
    
    In gen 4, WP is the reverse of gen 3. Instead of multiply, it divides 
    This means up to 200% earnings can occur. Note that perks are not considered.

    Which one to use?
    Use gen 1 for high WP scaling.
    Use gen 2 for high WP scaling but also preventing users with low balances to gain a lot.
    Use gen 3 for low WP scaling.
    Use gen 4 for WP scaling for use cases of WP giving more
    """

    match generation:
        case 1:
            return round(amount / calcWealthPower(u, decimal=True), acc)
        case 2:
            wp = calcWealthPower(u, decimal=True) - 1
            if wp < 1: wp = 1
            return round(amount / wp, acc)
        case 3:
            wealthPower = calcWealthPower(u)
            if wealthPower > 100:
                WPlost = 1 - ((wealthPower - 100) / 20 / 100)
                if WPlost < 0.5: WPlost = 0.5
            else:
                WPlost = 1

            return round(amount * WPlost, acc)
        case 4:           
            wealthPower = calcWealthPower(u, noperks=True)
            if wealthPower > 100:
                WPlost = 1 - ((wealthPower - 100) / 20 / 100)
                if WPlost < 0.5: WPlost = 0.5
            else:
                WPlost = 1

            return round(amount / WPlost, acc)

        case _:
            return round(amount, acc)

def calcAvgCredits() -> int:
    """Calculates average credits"""
    # Relative Power of Credits = (Credits ) / (Average Credits of Members)  

    usersDir = os.listdir('users')

    totalCredits, amtOfUsers = 0 ,0
    for file in usersDir:
        with open('users/' + file, 'r') as f:
            if file == "main.json": continue
            try:
                credits = float(json.load(f).get('credits'))
                if credits != 0: 
                    totalCredits += credits
                    amtOfUsers += 1
            except: pass

    try:
        return totalCredits / amtOfUsers
    except ZeroDivisionError:
        return 0


def calcScore(u: User, msg: bool = False) -> float | tuple[float, str]:
    """
    Calculates the score of a user
    
    Factors that affect score:
    - Ranking on leaderboard ((11 - current), cannot be under 0)
    - Average Credits earned (For up to 1k Cred, up to 50 can be obtained. Cannot be over 50)
    - Amount of transactions (Sqrt(x/2), cannot be over 50)
    - Average Unity earned (For up to 200 Unity, up to 20 can be obtained)
    - KCash Exchanged (For up to 10k exchanged, up to 20 can be obtained)

    As of 2025-05-20 (V.5.8), score slightly changes:
    - Score value is now scaled by 100x (50 >> 5000)
    - Score is an integer value
    - Adds Current Unity value
        - Each 1 Unity gives 5 Score (200 = 1000)
    """

    scores = {}
    # Leaderboard
    usersDir = os.listdir('users')

    users = {}
    for file in usersDir:
        if file == "main.json": continue
        try:
            with open(os.path.join("users", file), 'r') as f:
                try:
                    c = float(json.load(f)['credits'])
                    if c != 0: users[file.replace(".json", '')] = c
                except: pass
        except FileNotFoundError:
            pass

    sortedUsers = sorted(users.items(), key=lambda x:x[1], reverse=True)
    rge = len(sortedUsers)
    if rge > 10: rge = 0
    for i in range(len(sortedUsers)):
        usr = sortedUsers[i]
        if usr[0] == u.ID:
            ranking = i+1
            break
    else:
        ranking = 11

    scores['Leaderboard Ranking'] = (6 - ranking) * 200
    if scores['Leaderboard Ranking'] < 0:
        scores['Leaderboard Ranking'] = 0

    # Average earned
    try:
        with open(os.path.join("balanceLogs", str(u.ID)), 'r') as f:
            ballogs = f.readlines()
    except FileNotFoundError:
        return (0, "**Haven't played**: `0`") if msg else 0
    
    totalUnity = 0
    totalCred = 0

    for log in ballogs:
        try:
            totalCred += float(log.split(' ')[1])
            totalUnity += float(log.split(' ')[2])
        except IndexError: pass

    credScore = 2 * (totalCred / len(ballogs))
    if credScore > 5000: credScore = 5000
    scores['Average Credits'] = round(credScore)
    scores['Average Unity'] = round(10 * (totalUnity / len(ballogs)))

    # Amount of transactions
    transScore = ((u.getData('log')) / 2) ** 0.5 * 100
    if transScore > 5000: transScore = 5000
    scores['Number of Transactions'] = round(transScore)

    # KCash Exchanged
    scores['KCash Exchanged'] = round((1/5) * u.getData('kcashExchanged'))
    if scores['KCash Exchanged'] > 2000:
        scores['KCash Exchanged'] = 2000
    
    # Current Unity
    scores['Current Unity'] = round(5 * u.getData("unity"))

    
    # MSG or just send
    if msg:
        txt = []
        for name, score in scores.items():
            txt.append(f"**{name}**: `{round(score, 2)}`")
        return (round(sum(scores.values()), 2), "\n".join(txt))
    else:
        return round(sum(scores.values()), 5)


    
def calcScoreOld(u: User) -> int:
    """Calculates the score of a user"""
    score = 0
    try:
        # Average credits
        balances = []
        unitybal = []
        for line in tail("balanceLog.txt", 1000):
            if str(u.ID) in line:
                balances.append(
                    float(line.split("Now", 1)[1].split("CRED")[0].replace(" ", ""))
                )
                unitybal.append(
                    float(line.split("Now", 1)[1].split("CRED,", 1)[1].split("UNITY")[0].replace(" ", ""))
                )
        avgcredits = sum(balances) / len(balances)
        if avgcredits >= 0: score += avgcredits ** 0.5 
        print(score)

        # Average Unity
        avgunity = sum(unitybal) / len(unitybal)
        score += avgunity / 10
        print(score)
        # Current leaderboard
        usersDir = os.listdir('users')

        users = {}
        for file in usersDir:
            if file == "main.json": continue
            with open('users/' + file, 'r') as f:
                try:
                    c = float(json.load(f)['credits'])
                    if c != 0: users[file.replace(".json", '')] = c
                except: pass

        sortedUsers = sorted(users.items(), key=lambda x:x[1], reverse=True)
        for i in range(len(sortedUsers)):
            usr = sortedUsers[i]
            if usr[0] == u.ID:
                ranking = i+1
                break
        else:
            ranking = len(sortedUsers)
        score += ((len(sortedUsers) / ranking) * 10) ** 0.65
        print(score)
        # Current credits
        # if credits >= 0: score += u.getData('credits') ** 0.25 

        # Wealth power
        wp = calcWealthPower(u)
        if wp>0: score += wp ** 0.65 / 5
    except (ZeroDivisionError, KeyError, ValueError):
        score = 0

    return round(score)

def calcWealth(u: User, botCred = None) -> float:
    """
    Calculates the approximate wealth of a user.
    Wealth is the measure of how rich someone is based on not only by his/her credits, but also his/her Bot Stock % and Unity

    Mainly used for the calcWealthPower function. 

    Wealth is calculated using this formula:
    (Credits + BS% * Bot Credits)

    """

    if botCred is None: 
        botCred = User('main').getData('credits')

    userData = u.getData()

    return (
        (userData['credits'] + 
        userData['bs%'] * botCred / 100) 
    )

    
def calcTradeValue(u: User) -> float:
    """Calculates the trade value of a user"""
    bal = u.getData("credits")

    try:
        gold = u.getData("players").get("gold")
    except KeyError:
        gold = 0

    botbal = User('main').getData("credits")
    avgcredits = calcAvgCredits()

    tv = (
        (bal * 2 + (gold/5)) /
        (botbal + avgcredits)
    ) * calcWealthPower(User('main'))

    return round(tv, 2)

def calcValuePower(u: User) -> float:
    return round(calcTradeValue(u) / calcWealthPower(u, decimal=True), 2)

def getItem(user: User, item: str, case_insensitive: bool = True, count: bool = False) -> bool:
    """Returns True if the item is present on the user"""
    items = user.getData("items")
    c = 0
    for i in items:
        if (case_insensitive and i['item'].lower() == item.lower()) or (not case_insensitive and i['item'] == item):
            if count:
                c += 1
            else:
                return True
         
    if c == 0:
        if count: 
            return [False, 0]
        else:
            return False
    # Count must be active
    else: return [True, c]

def numStr(number) -> str:
    """Returns a number as a human-readable string"""
    try:
        return f"{number:>,.2f}"
    except TypeError:
        return "N/A"

def calcCredit(amount: int, user: User = None) -> float:
    """Calculates credit earnings. This should ideally be only used when positive amounts are gained. A user object should be specified."""
    
    if user is not None:
        unity = user.getData('unity')
        credits = user.getData('credits')
        wealth = calcWealth(user)
        data = user.getData()

        """ POSITIVES """
        # In Debt raise (15% Credit gain)
        if credits < 0:
            amount *= 1.15
        
        # Did not claim Daily (+2.5%)
        if time.time() - data["dailyTime"] > 60*60*12:
            amount *= 1.025

        # In Hourly (+10%)
        if time.time() - data["hourlyTime"] < 60*10:
            amount *= 1.10

        # Bot
        if str(user.ID) == "main":
            amount *= (1 + 2)

        # Prosperous Reset bonus
        if user.get_item('Prosperous Reset', True):
            amount *= (1 + 0.15)

        # Both set IGN and LFN (+2%)
        try:
            if data["IGN"] is not None and data["LFN"] is not None:
                amount *= 1.02
        except KeyError: pass

        # Excessive Unity (Every 1 above 100 grants +0.1%, up to 200)
        if unity > 100:
            amount *= (1 + (unity - 100) * 0.001) if unity <= 200 else 1.2


        """ NEGATIVES """
        # Negative unity subtraction
        if unity < 0:
            unityFee = round((100 - -unity) / 100, 2)
            amount *= unityFee

        # Rich I (-5% Credit gain)
        if wealth > 1000:
            amount *= 0.95
        
        # Rich II (-15% Credit gain)
        if wealth > 3000:
            amount *= 0.85

        # Rich III (-20% Credit gain)
        if wealth > 5000:
            amount *= 0.80

        # Too Rich (-0.001% Credit gain for every Wealth)
        if wealth > 50000:
            amount *= 1 + round((50000 - wealth) * 0.00001, 2)

        """ JOB """
        if data['job'] is not None:
            with open('jobs.json', 'r') as f:
                jobs = json.load(f)
            amount *= round(1 + jobs[data['job']]['credit perk'] / 100, 2)

    """ EVENTS """

    return round(amount, 2)


def calcCreditTxt(user: User) -> int:
    """Calculates credit earnings. This should ideally be only used when positive amounts are gained. A user object should be specified."""

    unity = user.getData('unity')
    credits = user.getData('credits')
    data = user.getData()

    amountTxt = {}

    """ POSITIVES """
    # In Debt raise (15% Credit gain)
    if credits < 0:
        amountTxt["In debt raise"] = 15
    
    # Did not claim Daily (+2.5%)
    if time.time() - data["dailyTime"] > 60*60*12:
        amountTxt["Daily unclaimed"] = 2.5

    # hourly
    if time.time() - data["hourlyTime"] < 60*10:
        amountTxt["Hourly boost"] = 10

    # BOT
    # hourly
    if str(user.ID) == "main":
        amountTxt["Is the main bot"] = 200
    
    # Reset bonus
    if user.get_item('Prosperous Reset', True):
        amountTxt["Reset Bonus"] = 15

    # Both set IGN and LFN (+2%)
    try:
        if data["IGN"] is not None and data["LFN"] is not None:
            amountTxt["IGN and LFN set"] = 2
    except KeyError: pass

    # Excessive Unity (Every 1 above 100 grants +0.1%, up to 200 (+10%))
    if unity > 100:
        amountTxt["Excess Unity"] = round((unity - 100) * 0.1, 5) if unity <= 200 else 1.2


    """ NEGATIVES """
    # Negative unity subtraction
    if unity < 0:
        unityFee = round((100 - -unity) / 100, 2)
        amountTxt["Negative Unity fee"] = -round(1 - unityFee, 3) * 100

    # Rich I (-10% Credit gain)
    if credits > 1000:
        amountTxt["Rich I (>1K)"] = -5

    
    # Rich II (-15% Credit gain)
    if credits > 3000:
        amountTxt["Rich II (>3K)"] = -15

    # Rich III (-20% Credit gain)
    if credits > 5000:
        amountTxt["Rich III (>5K)"] = -20

    # Too rich!
    if credits > 50000:
        amountTxt["Too Rich"] = round((50000 - credits) * 0.001, 2)

    """ JOB """
    if data['job'] is not None:
        with open('jobs.json', 'r') as f:
            jobs = json.load(f)
        amountTxt["[Job] " + data['job']] = jobs[data['job']]['credit perk']

    """ EVENTS """

    for i in amountTxt:
        if amountTxt[i] >= 0:
            amountTxt[i] = "+" + str(round(amountTxt[i], 5)) 

    return "\n".join(f"{perk}: `{percentAmt}% Credit earnings`" for perk, percentAmt in amountTxt.items())

def calculateRobDefense(member: discord.Member) -> int:
    """Calculate the Rob Defense level of a user"""

    """
    Factors that affect RDL
    * Target is offline or idle: Target Defense Rob -1
    * Already robbed that target within 5 minutes: Target Defense Rob +1
    * Target has `Lock`: Target Defense Rob +2
    * Has an Insight: Rob Attack +1 but Rob Defense -1 (Stacks up to 3 times)
    * Police / Pacifist job: Rob Defense +3
    """
    # Create user obj
    user = User(member.id)

    # Get Initial
    try:
        rob = user.getData()['rob']
        rdl = rob['def']
    except KeyError:
        user.update()
        rob = user.getData()['rob']
        rdl = rob['def']

    # IF offline
    if member.status in [discord.Status.offline, discord.Status.invisible, discord.Status.idle]:
        rdl -= 1

    # Already robbed
    if (time.time() - rob['attackedTime']) < 300:
        rdl += 2

    
    # Job roles
    match user.getData('job'):
        case "Police" | "Pacifist":
            rdl += 3

    # Insights
    rdl -= rob['insights']

    return rdl

def calculateRobAttack(member: discord.Member) -> int:
    """Calculate the Rob Attack level of a user"""

    """
    Factors that affect RAL
    * Has an Insight: Rob Attack +1 but Rob Defense -1 (Stacks up to 3 times)
    * You have `Rob Stealth`: Rob Attack +2
    * Robber job: Rob Attack +2
    * Pacifist job: Rob Attack -2
    """

    # Create user obj
    user = User(member.id)

    # Get Initial
    try:
        rob = user.getData()['rob']
        ral = rob['atk']
    except KeyError:
        user.update()
        rob = user.getData()['rob']
        ral = rob['atk']
    
    # Job roles
    match user.getData('job'):
        case "Robber":
            ral += 2
        case "Pacifist":
            ral -= 2

    # Insights
    ral += rob['insights']

    return ral

def convPyclassToType(pytype):
    print(pytype)
    if str(pytype)[:12] == "typing.Union":
        types = str(pytype)[13:-1]
        return types.replace(", ", " or ").replace("int", "Integer").replace("float", "Decimal").replace("str", "Text").replace("bool", "True/False")
    else:
        if pytype is int: return "Integer"    
        elif pytype is float: return "Decimal"
        elif pytype is str: return "Text"
        elif pytype is bool: return "True/False"
        elif pytype is discord.member.Member: return "User"
        else: return str(pytype)[8:-2]

def formatParamsOneLine(params: dict[str, discord.ext.commands.Parameter]) -> str:
    text = []
    for p in params:
        param = params[p]
        paramType = convPyclassToType(param.converter)
        if param.required:
            text.append(f"<{param.name}: {paramType}>")
        else:
            if param.default is not None:
                text.append(f"[{param.name}: {paramType} (default {param.default})]")
            else: 
                text.append(f"[{param.name}: {paramType}]")

    return " ".join(text)

def formatParamsMulti(command: discord.ext.commands.Command, prefix="!") -> str:
    # Param
    params = command.clean_params
    # e.g. <number> [text] 
    paramText = []
    paramDesc = []
    for p in params:
        # PARAM
        param = params[p]

        # Get type of the parameter
        paramType = convPyclassToType(param.converter)

        # If it is required, then do required text stuff
        if param.required:
            paramText.append(f"<{param.name}>")

            # Description to go along it
            paramDesc.append(f"{param.name}: {paramType}")

        else:                
            paramText.append(f"[{param.name}]")

            if param.default is not None:
                paramDesc.append(f"{param.name}: {paramType} (Default value: {param.default})")
            else: 
                paramDesc.append(f"{param.name}: {paramType}")

    return f"```yml\n{prefix}{command} " + " ".join(paramText) + "```" + ("```properties\n" + "\n".join(paramDesc) + "```" if len(paramDesc) > 0 else "")

def isDM(ctx: discord.ext.commands.Context):
    return isinstance(ctx.channel, discord.channel.DMChannel)

def mkDirNotExist(pathname: str, path = None) -> bool:
    if path is None:
        path = os.getcwd()

    if pathname not in os.listdir(path):
        os.mkdir(pathname)
        return True
    
    return False

class JSONIO:
    """Custom class for JSON IO-related things"""
    JSONCache: dict | list | None = None
    refreshCache = False

    def __init__(self, filename: str, cache: bool = False):
        self.filename = filename
        self.checkIfExists()

        if cache:
            self.__cacheJSON()

    def checkIfExists(self):
        if not os.path.isfile(self.filename):
            print(f"WARNING: JSON file {self.filename} is not in path. A new file is created")

            with open(self.filename, 'x') as f:
                f.write("{}")

            return True
        else:
            return False

    def __cacheJSON(self, data: dict | list): 
        # Cache
        self.JSONCache = data
        self.refreshCache = False

    def writeJSON(self, data: dict | list, indent: int = None):
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=indent)
        
        self.refreshCache = True
    
    def readJSON(self, cache: bool = False) -> dict | list:
        with open(self.filename, 'r') as f:
            data = json.load(f)
        
        if cache:
            self.__cacheJSON(data)
        
        return data
    
    def readCache(self) -> dict | list:
        """Reads the data in cache. If there is no cache, read it and cache it first before returning"""

        if self.JSONCache is None or self.refreshCache:
            return self.readJSON(cache=True)
        else:
            return self.JSONCache
  
    def returnData(self) -> dict | list:
        if self.JSONCache:
            return self.JSONCache
        else:
            return self.readJSON()       
        
    def writeKey(self, key: str, value, indent: int = None):
        data = self.returnData()
        data[key] = value
        return self.writeJSON(data)
        

    def readKey(self, key: str):
        return self.returnData().get(key)


    def __str__(self):
        return json.dumps(self.returnData())

    def deleteKey(self, key: str):
        data = self.returnData()
        del data[key]
        return self.writeJSON(data)


class DiminishRewards:
    def __init__(self, initialReward: int, minimumReward: int, reset: int, gen: int = 1):
        """
        Create a diminishing reward object.

        @param initialReward: The initial reward gained
        @param minimumReward: The minimum reward gained
        @param reset: Amount of seconds before the diminishing returns reset
        @param gen: The generation to use. 1 is a 1/x graph. 
        """

        self.rewardAmount = initialReward
        self.resetDuration = reset
        self.minReward = minimumReward

        self.users = {}

    def add_user(self, user: User):
        """
        Adds a user. You may directly use the reward method instead.
        This also resets the user's diminishing rewards.
        """

        self.users[user.ID] = [0, int(time.time())]

    def returnAmount(self, user: User) -> float:
        """
        Returns the amount rewarded for the user.
        It counts for credit earnings.
        """

        # Find if user exists
        if user.ID not in self.users or time.time() - self.users[user.ID][1] > self.resetDuration:
            self.add_user(user)
            self.users[user.ID][0] += 1 # Prevent /0

        # Reward
        amount = self.rewardAmount / self.users[user.ID][0]

        return round(max(calcCredit(self.minReward, user), calcCredit(amount, user)), 3)
    
    def reward(self, user: User) -> float:
        """
        Rewards a user with diminishing returns and returns the amount rewarded.
        """

        amount = self.returnAmount(user)
        user.addBalance(credits = amount)

        return amount
    
    def add_use(self, user: User):
        if user.ID not in self.users:
            self.add_user(user)
        
        self.users[user.ID][0] += 1
        print(self.users)