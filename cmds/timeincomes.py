import discord
from discord.ext import commands
from calculatefuncs import *

class TimeIncomes(commands.Cog):
    """Time based incomes"""
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(
        help = f"Get hourly reward",
        description = """The hourly reward increases Credit earnings for 10 minutes"""
    )
    async def hourly(self, message):
        user = User(message.author.id)
        data = user.getData()

        if 'hourlyTime' not in data:
            data["hourlyTime"] = 0

        if time.time() - data["hourlyTime"] < 60*60:
            embed = discord.Embed(title="On Cooldown!",description=f"You can claim the hourly reward <t:{int(data['dailyTime'] + 60*60)}:R>", color=0xFF0000)
            await message.send(embed=embed)
            return
        
        success = user.setValue("hourlyTime", int(time.time()))
        
        if success:      
            embed = discord.Embed(title="Hourly reward",description=f"Thank you for checking in with the bot!\nYou received a +10% Credits earning perk for 10 minutes", color=0x00FF00)
    
        else:
            embed = discord.Embed(title="An error occurred!",description=f"An unknown error occurred. Please try running the command again.", color=0xFF0000)


        await message.send(embed=embed)


    @commands.command(
        help = f"Get daily reward",
        description = """The daily reward gives an amount of Unity as well as Credits that scales with your wealth power.\nThe more wealth power you have, the less you earn.\nThe command be ran every 12 hours"""
    )
    async def daily(self, message):
        user = User(message.author.id)
        data = user.getData()
        if time.time() - data["dailyTime"] < 60*60*12:
            embed = discord.Embed(title="On Cooldown!",description=f"You can claim the daily reward <t:{int(data['dailyTime'] + 60*60*12)}:R>", color=0xFF0000)
            await message.send(embed=embed)
            return


        amount = 50 / (calcWealthPower(user, True) / 5)
        unityAmt = 3


        if random.randint(0,9) > 0:
            success = user.addBalance(
                credits=amount,
                unity=unityAmt
            )
            if success:      
                user.setValue('dailyTime', int(time.time()))
                user.saveAccount()
                embed = discord.Embed(title="Daily reward",description=f"Thank you for checking in with the bot!\nYour rewards:\n`+{numStr(amount)} Credits`\n`+{numStr(unityAmt)} Unity`", color=0x00FF00)
        
            else:
                embed = discord.Embed(title="An error occurred!",description=f"An unknown error occurred. Please try running the command again.", color=0xFF0000)
        else:
            user.setValue('dailyTime', int(time.time()) + 3720)
            user.saveAccount()
            credLost = calcWealthPower(user) / 2
            embed = discord.Embed(title="Daily failure",description=f"Where does the daily money come from?\nWhen you run the daily command, you actually take money away from the bot. Credits do not get created typically unless it is from the bot itself; you take the bot's money instead\nToday, the bot has decided to **rob** you instead of letting you steal it, making you lose `{numStr(credLost)} Credits` but gain `{numStr(unityAmt * 3 + 1)} Unity`.\nThe daily CD is also increased by 10%", color=0xFF0000)
            user.addBalance(
                credits=-credLost,
                unity=unityAmt*3 + 1
            )


        await message.send(embed=embed)

        
    @commands.command(
        help = f"Work\nFormat: {prefix}work [apply <job>]",
        description = f"""Apply for a job, then run {prefix}work to earn money. The job you apply for will give you a % increase in work output. The work output is the amount of money you earn from work. The job will also give you a % increase in credit earnings.\nThere is a slight chance (5%) that you will be fired from your job, causing you to lose `10 Unity` (scales with Wealth Power).\nThis 5% of being fired increases as you become more negative in Unity.\nApplying for a job initially costs `5 Unity` (scales with Wealth Power)""",
        aliases = ['job'],
        hidden = True
    )
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, message, cmd = None, value = None):
        user = User(message.author.id)
        data = user.getData()

        # Base gains
        baseCredits = 50 * calcInflation()
        baseUnity = 0.5

        with open('jobs.json', 'r') as f:
            jobs = json.load(f)

        # Get current job
        currentJob = data['job']
        
        if cmd is None:
            embed = discord.Embed(
                title="Work jobs",
                description=(
                    f"Apply using `{prefix}work apply <job>`" + 
                    ("\n" if currentJob == None else f"\nWork using `{prefix}work work`") +
                    "\nWork output is an additional money gain from work.\n" + 
                    "\n**Jobs:**\n" + 
                    "\n\n".join(f"""**{job}**: {jobs[job]['description']}\nCurrent base rates: `{numStr(baseCredits *(1 + jobs[job]['work output'] / 100))} Credits` and `{numStr(baseUnity * (1 + jobs[job]['work output'] / 100))} Unity`\nPerk: `{"+" + str(jobs[job]['credit perk']) if jobs[job]['credit perk'] >= 0 else jobs[job]['credit perk']}% Credit earnings`""" for job in jobs)
                ), 
                color=0xFF00FF
            )
        elif cmd == "work":

            if currentJob is None:
                embed = errorMsg("You must apply for a job first!")
            else:
                # Amount to fire
                # Should be int(-Unity/10) times, time >= 1, time E I
                fireamt = int(-user.getData('unity')/5)
                if fireamt < 0: fireamt = 1
                for i in range(fireamt):
                    if random.randint(0, 19) == 0:
                        # Fired
                        unityLost = 5 * calcWealthPower(user, decimal=True)

                        user.addBalance(unity=-unityLost)
                        user.setValue('job', None)

                        embed = discord.Embed(
                            title="Work",
                            description=(
                                f"Your boss fired you and you no longer have a job anymore!\nYou also lost `{unityLost} Unity`."
                            ),
                            color=0xFF0000
                        )
                        break
                else:
                    # Work
                    creditGain = calcCredit(baseCredits, user) * (1 + jobs[currentJob]['work output'] / 100)
                    unityGain = baseUnity * (1 + jobs[currentJob]['work output'] / 100)

                    # Job Bonuses
                    if currentJob == "Unifier": unityGain += 0.75
                    elif currentJob == "Banker": creditGain += (100 * calcInflation())

                    user.addBalance(credits=creditGain, unity=unityGain)

                    embed = discord.Embed(
                        title="Work",
                        description=(
                            f"You earned `{numStr(creditGain)} Credits` and `{numStr(unityGain)} Unity` from working as a {currentJob}"
                        ),
                        color=0x00FF00
                    )
                    # Directly return without resetting the CD
                    await message.send(embed=embed)
                    return

        elif cmd == "apply":
            # Apply for the job
            value = str(value).title()

            if value in jobs:
                unityLost = 5 * calcWealthPower(user, decimal=True)

                if user.getData('unity') < unityLost:
                    embed = errorMsg(title="Not enough balance!", description=f"You don't have enough Unity to apply for a job!\nJob cost: `{unityLost} Unity`\n\n## Tips:{WAYS_TO_EARN['unity']}")
        
                else:

                    user.addBalance(unity=-unityLost)
                    user.setValue('job', value)

                    embed = successMsg("Job applied", f"You paid `{numStr(unityLost)} Unity` to apply for the job of {value}!")

        else: embed = errorMsg("Command is not vaild!")

        await message.send(embed=embed)
        self.work.reset_cooldown(message)

