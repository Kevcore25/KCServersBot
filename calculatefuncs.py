"""Calculation functions"""

import users as usersFile
from users import User
import discord, os, json, time
import random

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
                if file == "main.json": continue

                credits = float(json.load(f).get('credits'))
                if credits != 0: 
                    totalCredits += credits
                    amtOfUsers += 1
            except: pass


    # Inflation % = Total Credits of Members / (Inflation amount * Amount of Members) x 100 (%)
    print(totalCredits, inflationAmt, amtOfUsers)
    inflationLvl = totalCredits / (inflationAmt * amtOfUsers)
    if inflationLvl < 1: inflationLvl = 1
    return inflationLvl


def calcWealthPower(u: User, decimal = False, noperks = False) -> int:
    """Calculates wealth power and returns a percentage"""
    # Relative Power of Credits = (Credits ) / (Average Credits of Members)  

    usersDir = os.listdir('users')

    totalCredits, amtOfUsers = 0 ,0
    for file in usersDir:
        with open('users/' + file, 'r') as f:
            if file == "main.json": continue
            try:
                credits = float(json.load(f).get('credits'))
                if credits <= 0: 
                    totalCredits += credits
                    amtOfUsers += 1
            except: pass

    try:
        credits = u.getData("credits")
        creditpower = (credits) / ((totalCredits - credits) / (amtOfUsers)) * 100
    except ZeroDivisionError:
        creditpower = 100

    if not noperks:
        # Pacifist job
        if u.getData('job') == "Pacifist":
            creditpower -= 50

    # Credit power should be at a minimum of 0% (Updated from -50%)
    # Otherwise, a bug would occur where users get negative credits due to commands having a (1 + Wealth Power%) multiplication. 
    if creditpower < 0:
        creditpower = 0

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


def calcScore(u: User, msg: bool = False) -> float | tuple[float, str]:
    """
    Calculates the score of a user
    
    Factors that affect score:
    - Ranking on leaderboard ((11 - current) ^ 1.2, cannot be under 0)
    - Average Credits earned (For up to 10k Cred, up to 50 can be obtained. Cannot be over 50)
    - Amount of transactions (Sqrt(x/2), cannot be over 50)
    - Average Unity earned (For up to 200 Unity, up to 40 can be obtained)
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

    scores['Leaderboard Ranking'] = (11 - ranking) ** 1.2

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

    credScore = (1 / 200) * (totalCred / len(ballogs))
    if credScore > 50: credScore = 50
    scores['Average Credits'] = credScore
    scores['Average Unity'] = (1/5) * (totalUnity / len(ballogs))

    # Amount of transactions
    transScore = ((u.getData('log')) / 2) ** 0.5
    if transScore > 50: transScore = 50
    scores['Number of Transactions'] = transScore

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
    * Police job: Rob Defense +3
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

    # Police job
    if user.getData('job') == "Police":
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
    
    # Robber job
    if user.getData('job') == "Robber":
        ral += 2
    

    # Insights
    ral += rob['insights']

    return ral

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import numpy as np

# Simulate some historical data (in reality, you'd use your actual data)                       
# Example data columns: 'hour_of_day', 'day_of_week', 'is_online' (0 for offline, 1 for online)
# data = {                                                                                     
#     'hour_of_day': [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],                       
#     'day_of_week': [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3],  # 0 = Monday, 1 = Tuesday, etc. 
#     'is_online': [1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0]  # Example labels                   
# }                                                                                             

def predict_discord_status(userID: int, hour_of_day, minute_of_hour, day_of_week) -> tuple[bool, float]:
    """Predict when someone will be online. """
    with open("userschedules.json", 'r') as f:
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

