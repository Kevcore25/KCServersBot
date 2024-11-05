"""Does a "reset." All balances are made the same"""
"score: system that determines the winner of the game every month (reset). when a reset happens everyone loses 50% of their balance plus additional 100 credits and that amount of credits is converted into kcash with the current exchange rate. The winner gets 100% more kcash and gets 3 gems, while 2nd gets 50% more kcash and 2 gems  and 3rd gets 1 gem. everyones balance is also set with current avg credits "

# 1 credit = ? kcash?
creditKcashRate = 0.1

import json, os

from users import User
from calculatefuncs import calcScore

# Obtain scores
usersDir = os.listdir('users')

users = []
totalCredits = 0
for file in usersDir:
    if file == "main.json": continue
    u = file.replace(".json", '')
    if User(u).getData("credits") != 0: 
        users.append(u)

        with open("users/"+file, 'r') as f:
            try:
                credits = json.load(f).get('credits')
                totalCredits += (credits / 2 - 100)
            except: pass

if totalCredits < 0: totalCredits = 0

scores = {}
totalScore = 0
for u in users:
    s = calcScore(User(u))
    scores[u] = s
    totalScore += s

sortedScore = sorted(scores.items(), key=lambda x:x[1], reverse=True)


avgscore = round(totalScore / len(sortedScore))

print(f"""
Average Score: {avgscore}

Average Credits Now: {totalCredits / len(users)}
""")


for i in range(3):
    usr = sortedScore[i]
    score = usr[1]
    user = usr[0]
    with open("users/"+user+'.json', 'r') as f:
        data = json.load(f)
        credits = data.get("credits")
        ign = data.get("ign")

    kcash = round(credits * creditKcashRate * (2 - (.5 * i)), 2)
    print(f"""
Place #{i+1}: {user} ({ign})
Score: {score}
Credits: {credits}
KCash Gained: {kcash} ({(2 - (.5 * i)) * 100}%)
Gems Gained: {3 - i}
""")
    # Add

    data['gems'] += 3 - i
    
    if "kcash" not in data:
        data['kcash'] = kcash
    else:
        data['kcash'] += kcash

    data['unity'] = 50 + (len(users) - i)

    with open("users/"+user+'.json', 'w') as f:
        json.dump(data, f)

users.append('main')
for user in users:
    with open("users/" + user + ".json", 'r') as f:
        data = json.load(f)

   # data['credits'] = round(totalCredits / len(users) - 100)
    data['credits'] = 500
    with open("users/" + user + ".json", 'w') as f:
        json.dump(data, f)


