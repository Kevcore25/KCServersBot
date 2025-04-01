"""Does a "reset." All balances are made the same"""
"score: system that determines the winner of the game every month (reset). when a reset happens everyone loses 50% of their balance plus additional 100 credits and that amount of credits is converted into kcash with the current exchange rate. The winner gets 100% more kcash and gets 3 gems, while 2nd gets 50% more kcash and 2 gems  and 3rd gets 1 gem. everyones balance is also set with current avg credits "


import json, os, time

from users import User
from calculatefuncs import calcScore

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

print(f"""
Average Score: {avgscore}
""")


for i in range(5):
    try:
        usr = sortedScore[i]
    except IndexError: 
        break

    score = usr[1]
    user = usr[0]
    with open("users/"+user+'.json', 'r') as f:
        data = json.load(f)
        credits = data.get("credits")
        ign = data.get("ign")

    print(f"""
Place #{i+1}: {user} ({ign})
Score: {score}
Credits: {credits}
Gems Gained: {(5 - i) ** 2}
""")
    # Add
    data['gems'] += 3 - i
 
    with open("users/"+user+'.json', 'w') as f:
        json.dump(data, f)

for user in users:
    with open("users/" + user + ".json", 'r') as f:
        data = json.load(f)

    data['credits'] = 50
    data['unity'] = 20

    data['items'] = {"Prosperous Reset": {"expires": [int(time.time() + 60*60*24*7)], "data": {}, "count": 1}}
    data['job'] = None
    data['bs%'] = 0
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

    with open("users/" + user + ".json", 'w') as f:
        json.dump(data, f)

# Main bot
with open("users/main.json", 'r') as f:
    data = json.load(f)

data['credits'] = 50000
data['unity'] = 0
data['items'] = {"Precognition": {"expires": [-1], "data": {}, "count": 1}, "Lock": {"expires": [-1, -1, -1, -1, -1], "data": {}, "count": 5}}
data['job'] = 'Player'
data['bs%'] = 100
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

with open("users/" + "main.json", 'w') as f:
    json.dump(data, f)
