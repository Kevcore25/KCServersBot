import discord
from discord.ext import commands
from calculatefuncs import *
import asyncio, sys
class AdminCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(
        help = "[ADMIN] Creates a gift code",
        hidden = True
    )
    async def creategift(self, message: discord.Message, amount: str, uses: int = 1, code: str | None = None):
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



    # ONLY FOR BETA BOT!
    # So dangerous, that it can ONLY be ran on the beta bot.
                        
    @commands.command(
        name='set',
        help = f"[DEBUG FEATURE] Sets a value for your account. Format: {prefix}set <key> <value>",
        hidden = True
    )
    async def setvaluecmd(self, message, key, value): # command is an argument
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
        if self.bot.application_id == 1228567790525616128 or message.author.id in [1220215410658513026, 1228567790525616128]:

            u = User(message.author.id)
            v = detect_data_type(value)
            u.setValue(key, v)

            await message.send(f"Set {key} to be {v} ({type(v)})")
        else:
            await message.send(embed=errorMsg(f"You do not have permission to use this command!"))

                

    @commands.command(aliases=['reload'], hidden=True)
    async def restart(self, ctx):
        if ctx.author.id in adminUsers:
            await self.bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name="me get updated"))
            embed=discord.Embed(title=f"Restarting the program...", description=f"... is it working?", color=0x00CCFF)
            await ctx.send(embed=embed, delete_after=3.0)
            os.execl(sys.executable, sys.executable, *sys.argv)


    @commands.command(hidden=True)
    async def reset(self, message):
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
Average Score: {avgscore}""")

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

                gemsGained = (5 - i) * 10

                msgs.append(basicMsg(
                    title=f"""Place #{i+1}""",
                    description = f"""
## <@{user}>
### **Total Score**: `{score}`
{calcScore(User(user), msg=True)[1]}
### Gems Gained: `{gemsGained}`"""))
                
                # Add
                data['gems'] += gemsGained
            
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

                data['credits'] = 50
                data['unity'] = 20

                data['items'] = {"Prosperous Reset": {"expires": [int(time.time() + 60*60*24*3)], "data": {}, "count": 1}}
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

                with open(os.path.join('users', user), 'w') as f:
                    json.dump(data, f)

            # Main bot
            with open("users/main.json", 'r') as f:
                data = json.load(f)

            data['credits'] = 100000
            data['unity'] = 0
            data['items'] = {"Precognition": {"expires": [-1], "data": {}, "count": 1}, "Lock": {"expires": [-1, -1, -1, -1, -1], "data": {}, "count": 5}}
            data['job'] = 'Player'
            data['bs%'] = 0
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