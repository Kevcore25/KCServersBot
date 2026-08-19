import discord
from discord.ext import commands
from calculatefuncs import *
import names 

class GambleGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(
        help = f"Beg for money",
        description = """Begging is the easiest way to earn money for new players. You can beg up to 3 times within 30 seconds.
When begging, you have a base chance of 80% of succeeding a beg. 
Certain items/jobs can increase this chance and thus significantly increase your profits.

When someone donates to you, you earn `0.05 Unity` and a random standard income from `0.5 Credits` to `20 Credits`
Otherwise, you may get caught, causing you to lose a base of `15 Credits`. If you do not have any Credits, you will be deducted `5 Unity`.

The detailed chances are listed below:
- Any amount between 0.5 to 1 Credits: 20%
- Any amount between 1 to 3 Credits: 40%
- 5 Credits: 20%
- 10 Credits: 15%
- 20 Credits: 5%
The expected standard income is `4.45 Credits` per beg, and for estimated expected values:
- For standard 80%: `0.56 Credits`, `0.02 Unity`
- For popularity: `~2.51 Credits`, `0.035 Unity`
- For beggar job: `1.67 Credits`, `0.025 Unity`
- For beggar+popularity: `~3.14 Credits`, `0.035 Unity`
-# SI Assumptions: 100% (or lower) WP, 100% Credit Efficiency (unless specified), 100% inflation"""
    )
    @commands.cooldown(3, 30, commands.BucketType.user) 
    async def beg(self, message, arg=None):
        user = User(message.author.id)

        # winAmount = round(avgCredits * random.randint(3, 5) / 200 + 1, 2)

        # Get win amount
        r = random.randint(1, 20)
        if r <= 4: winAmount = round(random.randint(50, 100)/100, 2)
        elif r <= 12: winAmount = round(random.randint(100, 300)/100, 2)
        elif r <= 16: winAmount = 5
        elif r <= 19: winAmount = 10
        else: winAmount = 20

        beggar = user.getData('job') == "Beggar"

        # Use standard income
        winAmount = standardIncome(winAmount, user)
        bold = ''

        # Popularity item
        if user.item_exists("Popularity"):
            r = random.randint(0, 9)
            bold += '**'
            user.delete_item("Popularity")
        elif beggar:
            r = random.randint(0, 5)
        else:
            r = random.randint(0, 4)
                        
        # Add a warning if user is too in debt
        if user.getData('unity') < -20 and arg is None:
            return await message.send(embed=errorMsg(f"You are running low on unity and should be saving up with commands such as daily.\nA high negative unity can be hard to recover and provides lower amounts of begging money.\nYou may choose ignore this warning by running this command with any arguments (e.g. `{prefix}beg ignore`)"))
            
        if r == 0:
            if user.getData('credits') < 0:
                user.addBalance(unity = -5)

                embed = discord.Embed(title="You got caught!",description=f"You got caught by the police!\nYou did not have anymore Credits, so you lost `5 Unity`.", color=0xFF0000)

            else:
                loseAmount = 15
                bold2 = ''
                if beggar and random.randint(1, 125) <= 6:
                    loseAmount = 50
                    bold2 = '**'

                loseAmount = round(loseAmount * calcInflation(), 2)

                user.addBalance(credits = -loseAmount, unity=-0.1)

                embed = discord.Embed(title="You got caught!",description=f"You got caught by the police!\nAs a result, you paid the police {bold2}`{numStr(loseAmount)} Credits`{bold2}.\n-# You also lost 0.1 Unity!", color=0xFF0000)

        else:
            # Sometimes gain 100% more
            if beggar and random.randint(0, 4) == 0:
                winAmount *= 2
                bold += '*'

            winAmount = calcCredit(winAmount, user)
            user.addBalance(credits = winAmount, unity = 0.05)

            gender = "male" if random.randint(0, 1) == 0 else "female"

            embed = discord.Embed(title="Begging successful!",description=f"{names.get_first_name(gender)} gave you {bold}`{numStr(winAmount)} Credits`{bold}.\n-# {'He' if gender == 'male' else 'She'} also earned you 0.05 Unity!", color=0x00FF00)

        await message.send(embed=embed)


    @commands.command(
        help = f"Invest money!",
        description = f"""Invest a portion of your money to the KCServers bot.
The amount you invest cannot exceed 10% of the current bot's balance.

There are 2 formats for this command:
* {prefix}invest <amount> - invests an amount of money to the bot
* {prefix}invest cash - cashes out the money you invested

**How does it work?**
You can invest a portion of your Credits to gain a *Bot Stock Percentage (Or BS%)*.
For example, if the bot has 10000 and you invest 1000, you will get a % equal to (1000 / 11000), which is about 9.09 BS%
In a few days, if the bot balance is now 15000 and you cash out, you will earn 1363.5 Credits, making about $363 gain.

Notice: You must wait at least 10 minutes until you can cash out after investing.
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
                await message.send(embed=errorMsg("You don't have enough Credits to invest that!"))
            
            # Fix negative investments
            elif amt <= 0:
                await message.send(embed=errorMsg("You cannot invest negative money!"))

            elif amt > 0.1 * botbal:
                await message.send(embed=errorMsg(f"The amount is over 10% of the bot balance! Do something lower than {round(botbal * 0.1, 2)}!"))

            else:
                # Check if already investing
                ubs = user.getData('bs%')
                bs = round(amt * 100 / (botbal + amt), 8)

                if ubs != 0 and arg2.lower() != "overwrite":
                    await message.send(embed=errorMsg(f"Already investing! Use {prefix}invest cash to cash out or overwrite it by doing {prefix}invest {amt} overwrite"))
                # If 0, do not invest to prevent scamming
                elif bs == 0.0:
                    await message.send(embed=errorMsg("The amount you invested is too small to gain a BS%!"))
                else:
                    user.setValue('bs%', bs)
                    user.addBalance(credits = -amt) # Bot should also get that balance

                    return await message.send(embed=successMsg(f"Invested {amt} Credits for a BS% of {bs}.\nYou must wait at least 10 minutes before cashing out."))

        except ValueError:
            if arg.lower() == "cash":
                
                bs = user.getData('bs%')

                if bs == 0:
                    await message.send(embed=errorMsg("You don't have an investment right now!"))
                else:
                    amt = round(botbal * bs / 100, 2) 

                    # Student decrease (-5%)
                    if user.getData('job') == "Student":
                        amt = round(amt * 0.95, 2)
                    # Banker increase
                    elif user.getData('job') == "Banker":
                        amt = round(amt * 1.05, 2)

                    user.addBalance(credits=amt) # bot should also lose that amount

                    user.setValue("bs%", 0)

                    await message.send(embed=successMsg(f"Cashed out! You gained {numStr(amt)} Credits!"))

            else:
                await message.send(embed=errorMsg("Invaild argument. Must be either a number, or exactly 'cash' to cash out your investment."))

        # Reset CD. CD is only for investments
        self.invest.reset_cooldown(message)