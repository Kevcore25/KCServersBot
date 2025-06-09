import discord
from discord.ext import commands
from calculatefuncs import *
import names 

class GambleGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(
        help = f"Beg for money",
        description = """There is a 1/3 Chance of getting caught, resulting in paying 2x of the original win amount.\nThe amount you win is determined by: `(Total Credits/4000 + 20) * randint(5,15)/10 * inflation%` and Wealth Power (Gen 1), where Total Credits is the total amount of credits every user has.\nYou can run this command 3 times in 30 seconds.\nIf you got caught, you will lose 1.75x the win amount (does not get affected by Credit Perks)\nIf you got caught while in debt, you will have to pay an additional `5 Unity` as a fine.\nIf you get caught while not in debt, you lose `0.1 Unity`\nHowever, if someone donated money to you, you gain `0.05 Unity`"""
    )
    @commands.cooldown(3, 30, commands.BucketType.user) 
    async def beg(self, message, arg=None):
        user = User(message.author.id)
        

        usersDir = os.listdir('users')

        totalCredits = 0

        for file in usersDir:
            if file == "main.json": continue
            with open('users/' + file, 'r') as f:
                totalCredits += json.load(f)['credits']

        winAmount = round((totalCredits/4000 + 1.5) * random.randint(5,15)/7 * calcInflation(), 2)

        winAmount = calcWPAmount(user, winAmount, generation=1)

        # Popularity item
        if user.item_exists("Popularity"):
            r = random.randint(0, 4)
            user.delete_item("Popularity")
        else:
            r = random.randint(0,2)
                        
        # Add a warning if user is too in debt
        if user.getData('unity') < -50 and arg is None:
            await message.send(embed=errorMsg(f"You are running low on unity and should be saving up with commands such as daily.\nA high negative unity can be hard to recover and provides lower amounts of begging money.\nYou may choose ignore this warning by running this command with any arguments (e.g. `{prefix}beg ignore`)"))
            return

        if r == 0:
            if user.getData('credits') < 0:
                user.addBalance(unity = -5)

                embed = discord.Embed(title="You got caught!",description=f"You got caught by the police!\nYou did not have anymore Credits, so you lost `5 Unity`.", color=0xFF0000)

            else:
                loseAmount = round(winAmount * 1.75, 3)

                user.addBalance(credits = -loseAmount, unity=-0.1)

                embed = discord.Embed(title="You got caught!",description=f"You got caught by the police!\nAs a result, you paid the police `{numStr(loseAmount)} Credits`.\n-# You also lost 0.1 Unity!", color=0xFF0000)

        else:
            winAmount = calcCredit(winAmount, user)
            user.addBalance(credits = winAmount, unity = 0.05)

            gender = "male" if random.randint(0, 1) == 0 else "female"

            embed = discord.Embed(title="Begging successful!",description=f"{names.get_first_name(gender)} gave you `{numStr(winAmount)} Credits`.\n-# {'He' if gender == 'male' else 'She'} also earned you 0.05 Unity!", color=0x00FF00)

        await message.send(embed=embed)


    @commands.command(
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
    async def invest(self, message, arg = "", arg2=''):
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
        self.invest.reset_cooldown(message)