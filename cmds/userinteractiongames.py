import discord
from discord.ext import commands
from calculatefuncs import *
import asyncio, games
from games import Players, PLAYER_TIER_COSTS

class InteractionGames(commands.Cog):
    """Games that involve other users"""
    def __init__(self, bot):
        self.bot = bot
    
    

    @commands.command(
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
    async def rob(self, message, target: discord.Member, ignorewarn = None):
        # This code should be cleaned up later
        # It is much more effective to use a class instead of functions within functions

        user = User(message.author.id)
        targetUser = User(target.id)

        if user.getData()['credits'] < 0:
            embed = discord.Embed(title="An error occurred!",description=f"Cannot rob when your balance is under 0!", color=0xFF0000)
            await message.send(embed=embed)
            self.rob.reset_cooldown(message)
            return
        if targetUser.getData()['credits'] < 0:
            embed = discord.Embed(title="An error occurred!",description=f"Cannot rob when the target's balance is under 0!", color=0xFF0000)
            await message.send(embed=embed)
            self.rob.reset_cooldown(message)
            return
        if target == message.author:
            embed = discord.Embed(title="An error occurred!",description=f"Cannot rob yourself!", color=0xFF0000)
            await message.send(embed=embed)
            self.rob.reset_cooldown(message)
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

        await message.send(embed = discord.Embed(
            title = "Unknown command",
            description = f"Did you mean `{prefix}p {message.invoked_with}`?",
            color = 0xFF0000
        ))


