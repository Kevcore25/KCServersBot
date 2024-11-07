"""Calculation functions"""


import users as usersFile
from users import User
import discord, os, json, time

with open("botsettings.json", 'r') as f:
    botsettings = json.load(f)

inflationAmt = botsettings['inflation amount']


# Source : chatgpt lol stackoverflow is UESLSES
def tail(filename, lines=100):
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

def get_prefix(val: float, accuracy: int = 1, symbol: str = "") -> str:
    """Returns a number with a shortened prefix, like 125356 into 125.3K"""
    # if round(value / 1000000000, accuracy) > 0:
    #     newValue = str(round(value / 1000000000, accuracy)) + "T"
    # elif round(value / 1000000, accuracy) > 0:
    #     newValue = str(round(value / 1000000, accuracy)) + "M"
    # elif round(value / 1000, accuracy) > 0:
    #     newValue = str(round(value / 1000, accuracy)) + "K"
    # else: 
    #     newValue = str(round(value, accuracy))
    
    # return newValue.replace('.0','') if accuracy == 0 else newValue

    if val >= 1_000_000_000_000:  # Really?
        val = str(int((val / 1_000_000_000_000), accuracy)) + "T"
    elif val >= 1_000_000_000:
        val = str(int((val / 1_000_000_000), accuracy)) + "G"
    elif val >= 1_000_000:
        val = str(int((val / 1_000_000), accuracy)) + "M"
    elif val >= 1_000:
        val = str(int((val / 1_000))) + "k"
    else:
        val = str(int(val))
    return val + symbol

def time_format(seconds: int) -> str:
    if str(seconds).isdigit():
        seconds = int(seconds)
        d = seconds // (3600 * 24)
        h = seconds // 3600 % 24
        m = seconds % 3600 // 60
        s = seconds % 3600 % 60
        temp = []
        if d > 0:
            temp.append(f'{d}D')
        if h > 0:
            temp.append(f'{h}H')
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
                credits = float(json.load(f).get('credits'))
                if credits != 0: 
                    totalCredits += credits
                    amtOfUsers += 1
            except: pass


    # Inflation % = Total Credits of Members / (Inflation amount * Amount of Members) x 100 (%)
    inflationLvl = totalCredits / (inflationAmt * amtOfUsers)
    if inflationLvl < 1: inflationLvl = 1
    return inflationLvl


def calcWealthPower(u: User, decimal = False) -> int:
    """Calculates wealth power and returns a percentage"""
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
        credits = u.getData("credits")
        creditpower = (credits) / ((totalCredits - credits) / (amtOfUsers)) * 100
    except ZeroDivisionError:
        creditpower = 100

    # Credit power should be at a minimum of -80%
    # Otherwise, a bug would occur where users get negative credits due to commands having a (1 + Wealth Power%) multiplication. 
    # This is now limited to / 0.2, which is 5x of a 0% wealth power
    if creditpower < -80:
        creditpower = -80

    return round(1 + creditpower/100, 2) if decimal else round(creditpower) 


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
def calcScore(u: User, returnValue = True, tailLen = 1000) -> float | tuple[float, dict]:
    try:
        score = {}
        score["Value Power"] = (2 * calcValuePower(u)) ** 0.5

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

        score["Leaderboard Ranking"] = (11 - ranking) if ranking < 11 else 0 

        unitybal = []
        for line in tail("balanceLog.txt", tailLen):
            if str(u.ID) in line:
                unitybal.append(
                    float(line.split("Now", 1)[1].split("CRED,", 1)[1].split("UNITY")[0].replace(" ", ""))
                )

        score["Unity differences"] = (max(unitybal) + min(unitybal) + (sum(unitybal) / len(unitybal))) ** 0.5
        try:
            score["Income Commands Used"] = u.getData("incomeCmdsUsed") ** (1/3)
        except KeyError:
            score["Income Commands Used"] = 0

        # IF Complex, set to -1

        for s in score:
            if isinstance(score[s], complex):
                score[s] = -1

        totalScore = 0
        for s in score:
            totalScore += score[s]
        return totalScore if returnValue else (totalScore, score)
    except Exception: return 0 if returnValue else (0, {"An error occurred": -1})
def calcCredit(amount: int, user: User = None) -> float:
    """Calculates credit earnings. This should ideally be only used when positive amounts are gained. A user object should be specified."""
    
    if user is not None:
        unity = user.getData('unity')
        credits = user.getData('credits')
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
            amount *= 2


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
        if credits > 10000:
            amount *= 0.95
        
        # Rich II (-15% Credit gain)
        if credits > 20000:
            amount *= 0.85

        # Rich III (-20% Credit gain)
        if credits > 30000:
            amount *= 0.80

        # Too Rich (-0.001% Credit gain for every Credit)
        if credits > 50000:
            amount *= 1 + round((50000 - credits) * 0.00001, 2)

        """ JOB """
        if data['job'] is not None:
            amount *= round(1 + data['job']['credit perk'] / 100, 2)

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
        amountTxt["Is the main bot"] = 100


    # Both set IGN and LFN (+2%)
    try:
        if data["IGN"] is not None and data["LFN"] is not None:
            amountTxt["IGN and LFN set"] = 2
    except KeyError: pass

    # Excessive Unity (Every 1 above 100 grants +0.1%, up to 200 (+10%))
    if unity > 100:
        amountTxt["Excess Unity"] = (1 + (unity - 100) * 0.1) if unity <= 200 else 1.2


    """ NEGATIVES """
    # Negative unity subtraction
    if unity < 0:
        unityFee = round((100 - -unity) / 100, 2)
        amountTxt["Negative Unity fee"] = -round(1 - unityFee, 3) * 100

    # Rich I (-10% Credit gain)
    if credits > 10000:
        amountTxt["Rich I (>10k)"] = -5

    
    # Rich II (-15% Credit gain)
    if credits > 20000:
        amountTxt["Rich II (>20k)"] = -15

    # Rich III (-20% Credit gain)
    if credits > 30000:
        amountTxt["Rich III (>30k)"] = -20

    # Too rich!
    if credits > 50000:
        amountTxt["Too Rich"] = round((50000 - credits) * 0.001, 2)

    """ JOB """
    if data['job'] is not None:
        amountTxt["[Job] " + data['job']['description']] = data['job']['credit perk']

    """ EVENTS """

    for i in amountTxt:
        if amountTxt[i] >= 0:
            amountTxt[i] = "+" + str(amountTxt[i]) 

    return "\n".join(f"{perk}: `{percentAmt}% Credit earnings`" for perk, percentAmt in amountTxt.items())

def calculateRobDefense(member: discord.Member) -> int:
    """Calculate the Rob Defense level of a user"""

    """
    Factors that affect RDL
    * Target is offline or idle: Target Defense Rob -1
    * Already robbed that target within 5 minutes: Target Defense Rob +1
    * Target has `Rob Padlock`: Target Defense Rob +2
    * Has an Insight: Rob Attack +1 but Rob Defense -1 (Stacks up to 3 times)
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
        rdl += 1
    
    # Insights
    rdl -= rob['insights']

    return rdl

def calculateRobAttack(member: discord.Member) -> int:
    """Calculate the Rob Defense level of a user"""

    """
    Factors that affect RDL
    * Has an Insight: Rob Attack +1 but Rob Defense -1 (Stacks up to 3 times)
    * You have `Rob Stealth`: Rob Attack +2
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
    
    # Insights
    ral += rob['insights']

    return ral