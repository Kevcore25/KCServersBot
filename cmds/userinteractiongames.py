import discord
from discord.ext import commands
from calculatefuncs import *
import asyncio, games, itertools
from games import Players, PLAYER_TIER_COSTS

class InteractionGames(commands.Cog):
    """Games that involve other users"""
    def __init__(self, bot):
        self.bot: discord.Client = bot
    
    

    @commands.command(
        help = f"Rob someone the modern way.\nFormat: {prefix}rob <target>",
        description = """
A new modern robbing system that rolls values instead of a fixed 33% to win.

**Dice Roll System**
This robbing system rolls a dice from 1 to a set amount. If your dice roll is higher than the opponent's roll, you win the rob. Otherwise, you lose the rob.
If you rolled the same as your target, a reroll is done.
By default with no upgrades or whatsoever, your Rob Attack has a level of 5, and your Rob Defense has a level of 5. This means that while robbing someone, you can roll up to a number of 5.
Certain actions and job professions can increase your Rob Attack and Rob Defense levels.

Also when failing a rob, you gain an *Insight*, increasing your chances of suceeding at the cost of your rob defenses decreasing.
Insights can stack up to 3 times and reset when succeeding a rob or being successfully robbed by another.

**Additional factors**
* Target is offline or idle: Target Defense Rob -1
* Already robbed that target within 5 minutes: Target Defense Rob +2
* Has an Insight: Rob Attack +1 but Rob Defense -1 (Stacks up to 3 times)
* Target has a Lock: Target Rob Defense +1 for each lock and an additional +2 Rob Defense
target

**Locks Information**
Previously, locks are items that require the attacker to buy a lock pick to bypass it. However, as of V.8.4, this has changed.
Now, you play a minigame with the lock pick:
- Robbing someone now has a combination. The number depends on the # of locks - 3 for 1 lock, and +1 for each additional lock (thus up to 5).
- You are asked to input a binary combination of length C (e.g. 00100)
- After you are done inputting, it will show HOW MANY combinations are correct.
- You are allowed 3 attempts, but with a 30 second time limit.
- Every rob generates the combination on the spot.
- Locks are broken based on this formula: `Matching Combinations - 2`. Cannot be under 0.
- Picking the lock removes the Lock and you gain `+1 Rob Attack Level` but losing removes your Rob Attack Level equal to number of unfound combinations.
- Robbing the Bot plays a modified version of the minigame...

**Amounts**
Win Amount: 
The amount you earn by successfully robbing someone is 10% of the target's balance.
The amount will be subtracted from the target's balance and will be given to you.

Lose Amount:
The amount you lose by failing to rob someone is based on the amount of Unity you have.
You also lose `5 Unity` when getting caught.
However, when failing a rob, there is a chance you do not get caught, and you won't lose anything.
The formula for lose amount is ||*`max(50, 100 - Unity)`*||
The formula for the catch chance is ||_`100% - (Chance of succeeding)^2`_||

**Unity in robbing**
Negative unity increases the Target's RDL in addition to balance difference.
The formula for this is ||_`(Original RDL) * (1 + (Your Unity / 20) ^ 2), (Your Unity) < 0`_||
    """,
        aliases = ["newrob"]
    )
    @commands.cooldown(1, 30, commands.BucketType.user) 
    async def rob(self, message: discord.ext.commands.Context, target: discord.Member, ignorewarn = None):
        # This code should be cleaned up later
        # It is much more effective to use a class instead of functions within functions
        # Prevent execution if this is in a DM channel
        if isDM(message):
            await message.send(embed=errorMsg("This command cannot be ran in a DM channel!"))
            return
        
        user = User(message.author.id)
        targetUser = User(target.id)

        if targetUser.getData()['credits'] < 0:
            embed = discord.Embed(title="An error occurred!",description=f"Cannot rob when the target's balance is under 0!\nAt least, not yet (coming soon!)", color=0xFF0000)
            await message.send(embed=embed)
            self.rob.reset_cooldown(message)
            return
        if target == message.author:
            embed = discord.Embed(title="An error occurred!",description=f"Cannot rob yourself!", color=0xFF0000)
            await message.send(embed=embed)
            self.rob.reset_cooldown(message)
            return
        
        data = user.getData()

        if data['credits'] < 0 and data['unity'] < 0:
            embed = discord.Embed(title="An error occurred!",description=f"Cannot rob when you are at negative Unity and Credits!", color=0xFF0000)
            await message.send(embed=embed)
            self.rob.reset_cooldown(message)
            return
        
        # Get variables
        userBal = data['credits']
        targetBal = targetUser.getData()['credits']

        # Determine if the user is robbing the bot
        # Change rewards/gameplay if it is
        robbingBot = target.id == self.bot.user.id
        
       # Get amounts
        if robbingBot:
            winAmount = 200
            loseAmount = 50
        else:
            winAmount = round(targetBal / 10, 2)
            loseAmount = max(50, 100-data['unity'])

        userRAL = calculateRobAttack(message.author)
        targetRDL = calculateRobDefense(target)

        # Warn
        if ignorewarn is None and (targetRDL / userRAL) > 3 and not robbingBot:
            await message.send(embed=discord.Embed(
                title = "Warning",
                description = f"""The target's base Rob Defense Level ({targetRDL}) is more than 3x compared to your base Rob Attack Level ({userRAL})\nYou are very likely to lose this robbery.\nYou may ignore this warning by running the command with any arguments (e.g. `{prefix}rob {target.global_name} ignore`)""",
                color=0xFFAA00
            ))
            self.rob.reset_cooldown(message)
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

        async def lose(caught: bool = True):
            # Lose money
            if caught:
                if user.getData('credits') >= 0:
                    user.addBalance(credits = -loseAmount)
                    targetUser.addBalance(credits = loseAmount)
                    unityLoss = -5 if data['job'] == "Robber" else -3
                    user.addBalance(unity = unityLoss)
                    if targetUser.getData('job') == "Police":
                        targetUser.addBalance(unity = -unityLoss)

                else:
                    unityLoss = -15

                    user.addBalance(unity = unityLoss)
                    if targetUser.getData('job') == "Police":
                        targetUser.addBalance(unity = -unityLoss)

                if targetUser.get_item("Rob Alerts"):
                    await direct_message(target, embed = discord.Embed(title = "A user attempted to rob you", description=f"{message.author.mention} tried to rob you, but luckily failed.\nThe police also caught {message.author.mention} and you were paid `{loseAmount} Credits`.\nYou have `{targetUser.get_item("Lock", False).get("count", 0)}` locks left." + (f'\nSince you are a Police, you were also paid `{-unityLoss} Unity`.' if targetUser.getData('job') == "Police" else ''), color=0xffaa00))

            elif targetUser.get_item("Rob Alerts"):
                await direct_message(target, embed = discord.Embed(title = "A user attempted to rob you", description=f"{message.author.mention} tried to rob you, but luckily failed.\nHowever, the police never caught {message.author.mention} and you were not paid.\nYou have `{targetUser.get_item("Lock", False).get("count", 0)}` locks left.", color=0xffaa00))

            # Rob stats
            if robGet(user, 'insights') < 3:
                robAdd(user, "insights", 1)

            wl = robGet(user, "won/lost")
            robSet(user, "won/lost", [wl[0], wl[1]+1])

        # Attacked times
        robSet(user, "attackTime", int(time.time()))
        robSet(targetUser, "attackedTime", int(time.time()))

        # Lock
        bonusAtk = 0
        if targetUser.get_item("Lock", onlydetermine=True): 
            # 75% to break lock if user has lock pick
            if user.get_item("Lock Pick", onlydetermine=True):
                """
                NEW LOCK PICK SYSTEM:
                WITH MINIGAME, SUCCESSFUL COMPLETION GIVES +3 ATK BUT FAILURE GIVES - ATK
                
                BASIC DESCRIPTION:
                Lock picks are changed so that it simulates a real lock pick
                Depending on number of locks the target has, it gains # of combinations equal to 2 + # of Locks (e.g. 1 lock = 3 and 3 locks = 5)
                This combination is set as a sequence of binary numbers, such as 101 for a 1 lock user
                User is prompted to ask for a binary level, like 001 for 3 combinations
                Then the user is informed about how many combinations they got right (e.g. in this case, 2, as the 2 and 3 slots are correct)
                The user gets to retry, equal to the combination amount
                """
                
                
                C = 10 if robbingBot else 2 + targetUser.get_item("Lock", onlydetermine=False).get("count", 1)

                ANS = ''.join([str(random.randint(0,1)) for i in range(C)])
                highestFound = 0
                found = 0
                END_TIME = time.time() + (60 if robbingBot else 30) + 5
                answers = []
                broken = False
                auto = False
                autoFirst = False
                autoCombos = []
                autoIndex = 0

                ATTEMPTS = 7 if robbingBot else 3

                for i in range(ATTEMPTS):
                    if broken: break
                    em = discord.Embed(
                        title = "Rob Results",
                    description = f"""{target.mention} has {C-2} lock(s) and you need to pick it!
A **{C}-length** BINARY sequence of numbers is generated (e.g. {''.join([str(random.randint(0,1)) for i in range(C)])})
Please send a **{C}-length** binary sequence of numbers to try and guess it!
You will be informed on how many combinations were matching.

Attempts left: `{ATTEMPTS-i}`. Time remaining: <t:{int(END_TIME)}:R>
__Guesses__
{'**AUTOMATICALLY GENERATING GUESSES**' if auto else ''}
{'\n'.join(f'`{a}`: {c} matching' for a, c in answers)}
""",
                        color = 0xFF00FF,
                    )

                    await msg.edit(embed=em)

                    # Get Valid XXX 
                    userInput = ""
                    while not (len(userInput) == C and userInput.isdigit() and len(userInput.replace("0", "").replace("1","")) == 0) and not auto:
                        if userInput.lower() in {"exit", "quit"}:
                            return await message.send(embed=errorMsg("Exited the lock pick minigame.", title="Robbing failed"))
                        try:
                            if not auto:
                                ui = await self.bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=int(END_TIME - time.time() + 1))
                                userInput = ui.content.lower()

                            if userInput == "auto":
                                auto = True
                                try:
                                    await ui.delete()
                                except discord.errors.Forbidden:
                                    pass
                                break

                            if (len(userInput) == C and userInput.isdigit() and len(userInput.replace("0", "").replace("1","")) == 0):
                                # Calc # of found
                                found = 0
                                for j in range(C):
                                    if userInput[j] == ANS[j]:
                                        found += 1
                                highestFound = max(highestFound, found)
                                answers.append((userInput, found))

                                try:
                                    await ui.delete()
                                except discord.errors.Forbidden:
                                    pass

                        except (TimeoutError, asyncio.exceptions.TimeoutError):
                            broken = True
                            break
                    
                    if auto:
                        if not autoFirst:
                            # Get number of 1s to put
                            userInput = "1" * C
                            found = 0
                            for j in range(C):
                                if userInput[j] == ANS[j]:
                                    found += 1
                            autoFound = found
                            autoCombos = list(itertools.combinations(range(C), autoFound))[::-1]
                            autoFirst = True
                        else:
                            ones = autoCombos[autoIndex % len(autoCombos)]
                            userInput = ''.join('1' if j in ones else '0' for j in range(C))
                            autoIndex += 1

                        # Calc # of found
                        found = 0
                        for j in range(C):
                            if userInput[j] == ANS[j]:
                                found += 1
                        highestFound = max(highestFound, found)
                        answers.append((userInput, found))
                        

                    if found == C:
                        break

                    
                # Final
                if found == C:
                    bonusAtk += 145 if robbingBot else 1
                    em = discord.Embed(
                        title = "Rob Results",
                        description = f"""Robbing {target.mention}...

You managed to find all possible combinations and removed their locks!
The correct combination was `{ANS}`.
You also gained `+{bonusAtk} Rob Attack Level(s)`!""",
                        color = 0x00FF00,
                    )

  

                else:
                    bonusAtk = highestFound - C
                    em = discord.Embed(
                        title = "Rob Results",
                        description = f"""Robbing {target.mention}...

Unfortunately, you did not manage to find all matching combinations.
The combination was `{ANS}` and your highest was `{highestFound} matching combinations`.
Thus you broke `{max(0, highestFound-2)}` locks.

You were penalized `{bonusAtk} Rob Attack Levels` as a result.""",
                        color = 0xFF0000,
                    )

                # Delete based on found-2, cannot be lower than 0
                # Don't delete for bot
                if not robbingBot:
                    for i in range(max(0, highestFound-2)):
                        targetUser.delete_item("Lock")

                # Remove 1 lock pick
                user.delete_item("Lock Pick")

                await msg.edit(embed=em)

            else:
                em = discord.Embed(
                    title = "Rob Results",
                    description = f"""Robbing {target.mention}...

Unfortunately, {target.mention} has a lock, and you did not bring a lock pick to break it.
You will now try to steal his/her money anyway with the lock, though it might be challenging!
(`-2 Rob Attack Levels`)""",
                    color = 0xFF0000,
                )
                bonusAtk -= 2

                await msg.edit(embed=em)

            await asyncio.sleep(5)
        
        bonusDef = 2 + targetUser.get_item("Lock", onlydetermine=False).get("count", -2)

        # Calculate chance
        total = won = 0
        for A in range(max(1,userRAL+bonusAtk)):
            for D in range(max(1, targetRDL+bonusDef)):
                if A != D:
                    total += 1
                    if A > D:
                        won += 1

        # Logic
        # For loop is for rerolls
        for i in range(10): # Limit 10
            
            userRoll = random.randint(1, max(1,userRAL+bonusAtk))
            targetRoll = random.randint(1, max(1, targetRDL + bonusDef))

            if i == 9:
                userRoll = 100 + targetRoll

            if userRoll == targetRoll: 
                winTxt = f"Close! Rerolling... (Rerolled {i+1} time(s))"
            elif userRoll > targetRoll:
                winTxt = f"You successfully robbed {target.mention} and stole `{winAmount} Credits`!"

                # Robbers gain +5 Credits
                bonusCred = 0
                if data['job'] == "Robber":
                    bonusCred = standardIncome(5, user)
                    winTxt += f"\nYou also gained a bonus `+{bonusCred} Credits` as a successful robber."

                # Win Money
                user.addBalance(credits = winAmount + bonusCred)
                targetUser.addBalance(credits = -winAmount)

                # Rob stats
                robSet(user, "insights", 0)
                robSet(targetUser, "insights", 0)

                wl = robGet(user, "won/lost")
                robSet(user, "won/lost", [wl[0]+1, wl[1]])

                if targetUser.get_item("Rob Alerts"):
                    await direct_message(target, embed = discord.Embed(title = "A user attempted to rob you", description=f"You found that {message.author.mention} just robbed you and stole `{winAmount} Credits`.\nYou have `{targetUser.get_item("Lock", False).get("count", 0)}` locks left.", color=0xff0000))


            elif targetRoll > userRoll:
                # Lose Unity if negative
                caught = ((won/total) * 10000) < random.randint(1, 10000)
                if caught:
                    if user.getData('credits') >= 0:
                        match random.randint(1,3):
                            case 1: winTxt = f"Unfortunately, {target.mention} caught you and you were forced to pay `{loseAmount} Credits`"
                            case 2: winTxt = f"Unfortunately, the Police caught you and you were fined `{loseAmount} Credits` to {target.mention}"
                            case 3: winTxt = f"You slipped and fell, causing `{loseAmount} Credits` to be lost after being embarrassed by {target.mention}"
                    else:
                        match random.randint(1,3):
                            case 1: winTxt = f"Unfortunately, {target.mention} caught you and you lost `10 Unity` out of embarrassment"
                            case 2: winTxt = f"Unfortunately, the Police caught you and you were shamed and lost `10 Unity`"
                            case 3: winTxt = f"You slipped and fell, causing `10 Unity` to be lost after being embarrassed by {target.mention}"
                else:
                    match random.randint(1,3):
                        case 1: winTxt = f"Unfortunately, you did not manage to steal from {target.mention}\nHowever, you were also not caught in the process!"
                        case 2: winTxt = f"Unfortunately, you never had a good opportunity to steal from {target.mention}\nHowever, you were also not noticed!"
                        case 3: winTxt = f"You lost track of where {target.mention} went, losing the opportunity to steal some Credits\nLuckily, you were not caught attempting to do so."
                await lose(caught)

            em = discord.Embed(
                title = "Rob Results",
                description = f"""Robbing {target.mention}...

**Your Roll**: `{userRoll}`
**{target.mention}'s Roll**: `{targetRoll}`

**{winTxt}**
-# Your Rob Attack Level: `{max(1,userRAL+bonusAtk)}` (`{userRAL}{'+' if bonusAtk >= 0 else ''}{bonusAtk}`)
-# Target Rob Defense Level: `{max(1,targetRDL+bonusDef)}` (`{targetRDL}{'+' if bonusDef >= 0 else ''}{bonusDef}`)
-# Win chance: {round(won/total*100,1)}%""",
                color = 0xFF00FF,
            )

            await msg.edit(embed=em)

            # End if not reroll; otherwise wait 3 sec
            if userRoll != targetRoll:
                break
            else:
                await asyncio.sleep(3)

    async def msginput(self, ctx: discord.Message, text: str | None, timeout: int = 60) -> str:
        if text is not None: await ctx.send(text)
        ui = await self.bot.wait_for("message", check=lambda msg: msg.author == ctx.author, timeout=timeout)
        return str(ui.content)


    @commands.command(
        name="players",
        help = f"Format: {prefix}players <option>",
        aliases = ['play', 'p', 'mc', 'pop', 'pops']
    )
    async def players_cmd(self, message, cmd: str = ".", *args):
        u = Players(
            message.author.id
        )
        # Prevent execution if this is in a DM channel
        if isDM(message):
            await message.send(embed=errorMsg("This command cannot be ran in a DM channel!"))
            return
        
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

                    
                    ui = await self.msginput(message, f"Set default {i} to be ? (Values (tiers): basic, iron, gold, diamond)")
                    if ui not in PLAYER_TIER_COSTS:
                        await message.send("Invalid!")
                        return
                    else: 
                        a[i] = ui
                        

                    
                ui = await self.msginput(message, f"Set default weapon (tier_[bow, sword, axe]) to be ?")
                if ui.split("_")[0] not in PLAYER_TIER_COSTS and ui.split("_")[1] not in ("bow", "sword", "axe"):
                    await message.send("Invalid!")
                    return
                else: 
                    a['sword'] = ui

                await message.send(u.set_default(a['armor'], a['shields'], a['sword'], a['pickaxe']))
            case "upgrade" | "update": await message.send(u.upgrade())
            case "bal" | "acc" | "pf" | "balance" | "account" | "profile":

                if len(args) > 0:
                    userid = self.bot.get_user(int(args[0].replace("<",'').replace(">",'').replace("@",''))).id
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
                    userid = self.bot.get_user(int(args[0].replace("<",'').replace(">",'').replace("@",''))).id

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

        
    @commands.command(
        help = f"Has aliases for commands relating to Players",
        aliases = ['mine', 'upgrade', 'loadout', 'update', 'depopulate', 'populate', 'fight', 'kill'],
        hidden = True
    )
    async def players_redir_commands(self, message: discord.Message):
        # Prevent execution if this is in a DM channel
        if isDM(message):
            await message.send(embed=errorMsg("This command cannot be ran in a DM channel!"))
            return

        await message.send(embed = discord.Embed(
            title = "Unknown command",
            description = f"Did you mean `{prefix}p {message.invoked_with}`?",
            color = 0xFF0000
        ))


