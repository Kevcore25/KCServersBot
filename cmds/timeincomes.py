import discord
from discord.ext import commands
from calculatefuncs import *
import yaml
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
            embed = discord.Embed(title="On Cooldown!",description=f"You can claim the hourly reward <t:{int(data['hourlyTime'] + 60*60)}:R>", color=0xFF0000)
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
        description = """The daily reward gives 1 Unity as well as 10 Credits that scales with your wealth power (Gen 2).\nThe more wealth power you have, the less you earn.\nThe command be ran every 12 hours\nThere is a chance of failing a daily reward, which will result in a loss of 10 Credits (gen 4 WP scaling) but gaining 1.5 Unity\nIf the user has negative Unity, the user gains 2 Unity instead of 1."""
    )
    async def daily(self, message):
        user = User(message.author.id)
        data = user.getData()
        if time.time() - data["dailyTime"] < 60*60*12:
            embed = discord.Embed(title="On Cooldown!",description=f"You can claim the daily reward <t:{int(data['dailyTime'] + 60*60*12)}:R>", color=0xFF0000)
            await message.send(embed=embed)
            return


        amount = calcWPAmount(user, 10, generation=2)
        unityAmt = 1 if data['unity'] >= 0 else 2

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
            credLost = calcWPAmount(user, 10, generation=4)
            embed = discord.Embed(title="Daily failure",description=f"Where does the daily money come from?\nWhen you run the daily command, you actually take money away from the bot. Credits do not get created typically unless it is from the bot itself; you take the bot's money instead\nToday, the bot has decided to **rob** you instead of letting you steal it, making you lose `{numStr(credLost)} Credits` but gain `{numStr(1.5)} Unity`.\nThe daily CD is also increased by 10%", color=0xFF0000)
            user.addBalance(
                credits=-credLost,
                unity=1.5
            )


        await message.send(embed=embed)

        
    @commands.command(
        help = f"Work\nFormat: {prefix}work [apply <job>]",
        description = f"""Apply for a job, then run {prefix}work to earn money. The amount you earn is scaled with Credit Earnings and Wealth Power\nThere is a slight chance (5%) that you will be fired from your job, causing you to lose `10 Unity` (scales with Wealth Power).\nThis 5% of being fired increases as you become more negative in Unity.\nApplying for a job initially costs `5 Unity`\n\nWork uses Gen 3 WP scaling (Every 20% Wealth Power after 100% results in -1% earnings, up to -50% earnings) for both earnings and unity losses.""",
        aliases = ['job'],
    )
    async def work(self, message, cmd = None, value = None):
        user = User(message.author.id)
        data = user.getData()

        with open('jobs.yml', 'r') as f:
            jobs = yaml.safe_load(f)

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
                    "\n\n".join(f"""**{job}**: {jobs[job]['Description']}\nCurrent base rates: `{numStr(jobs[job]['Credits'])} Credits` and `{numStr(jobs[job]['Unity'])} Unity`\nPerk: `{"+" + str(jobs[job]['Credit Efficiency']) if jobs[job]['Credit Efficiency'] >= 0 else jobs[job]['Credit Efficiency']}% Credit Efficiency`\nWork Threshold: `{numStr(jobs[job]['Unity Threshold'])} Unity`""" for job in jobs)
                ), 
                color=0xFF00FF
            )
        elif cmd == "work":
            if time.time() - data["workTime"] < 60*60:
                embed = discord.Embed(title="On Cooldown!",description=f"You can work again <t:{int(data['workTime'] + 60*60)}:R>", color=0xFF0000)
                await message.send(embed=embed)
                return
            elif currentJob is None:
                embed = errorMsg("You must apply for a job first!")
            else:
                # Amount to fire
                # Should be int(-Unity/10) times, time >= 1, time E I
                unity = data['unity']

                fireamt = max(1, int(-unity/5))

                for i in range(fireamt):
                    # Fail chance = 5% + 1% for every 1 unity under threshold
                    # Fail chance caps at 50
                    unityThres = jobs[currentJob]['Unity Threshold']

                    failchance = min(
                        50, 
                        5 + (1 * int(unityThres - unity) if unity < unity else 0)
                    )

                    if random.randint(0, 99) < failchance and currentJob != "Pacifist":
                        # Fired
                        unityLost = calcWPAmount(user, 5, generation=4)

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
                    creditGain = standardIncome(jobs[currentJob]['Credits'], user)
                    unityGain = jobs[currentJob]['Unity']

                    # Bonus for gambler
                    if currentJob == "Gambler":
                        lastCG = user.getData("lastCG")

                        if lastCG > 10:
                            lastCG = 10

                        creditGain = round(creditGain * lastCG, 3)
                        user.setValue("lastCG", 1)
                    # Regulate bot with Banker
                    elif currentJob == "Banker":
                        u = User('main')
                        u.addBalance(-1000)
                        u.addBalance(calcCredit(1000, u))


                    user.addBalance(credits=creditGain, unity=unityGain)

                    embed = discord.Embed(
                        title="Work",
                        description=(
                            f"You earned `{numStr(creditGain)} Credits` and `{numStr(unityGain)} Unity` from working as a {currentJob}"
                        ),
                        color=0x00FF00
                    )

                    user.setValue('workTime', int(time.time()))

                    await message.send(embed=embed)
                    return

        elif cmd == "apply":
            # Apply for the job
            value = str(value).title()

            if value in jobs:
                # Get Unity threshold
                unityThres = jobs[value]['Unity Threshold']
                if user.getData('unity') >= unityThres:
                    user.setValue('job', value)
                    user.addBalance(unity = -5)
                    embed = successMsg("Job applied", f"You applied for the job of {value}!\nYou lost 5 Unity during the process.")
                else:
                    embed = errorMsg("You do not meet the minimum Unity threshold to apply for this job!")
            else:
                embed = errorMsg("That job does not exist!")

        else: embed = errorMsg("Command is not vaild!")

        await message.send(embed=embed)
