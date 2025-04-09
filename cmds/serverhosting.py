import discord
from discord.ext import commands
from calculatefuncs import *

class TemplateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
   
    @commands.command(
        help = f"Create a low-end MC server",
        description = f"""Due to hardware constraints, the MC server would only have 1 GB of RAM on a shared CPU thread.
Maximum of 2 MC servers can be ran at once, and only 1 per user is allowed.

Depending on what server provider you choose, hosting a server costs various amounts of Credits and Unity per minute.
Current providers:
    local: 0.025 Unity/min, 0.1 Credits/min

Steps to host:
1. Choose a provider (recommended `local`)
2. Choose configuration (automatically `low`)
3. Choose software. (either `paper` or `fabric`)
    See *Software* section for more details
4. Choose Minecraft version
5. Add any additional features (e.g. KMCEV2, RLWorld Datapack, Guns Datapack)
6. Host!

Software:
Both PaperMC (`paper`) and Fabric (`fabric`) have outstanding performance compared to the vanilla jar file.
Fabric tends to be better than PaperMC due to its low modification of vanilla features (e.g. TNT duping).
KMCEV2 works __best__ in a PaperMC server but can still work in a Fabric server.
**If you are not sure what to choose, choose `fabric`.**
Fabric comes with performance enhancing mods (e.g. Lithium).
PaperMC comes with ViaVersion and FastAsyncWorldEdit (FAWE).
""",
        hidden = True
    )
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def createserver(self, message, cmd = None, value = None):
        user = User(message.author.id)
        data = user.getData()

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
                    "\n\n".join(f"""**{job}**: {jobs[job]['description']}\nCurrent base rates: `{numStr(jobs[job]['credits'])} Credits` and `{numStr(jobs[job]['unity'])} Unity`\nPerk: `{"+" + str(jobs[job]['credit perk']) if jobs[job]['credit perk'] >= 0 else jobs[job]['credit perk']}% Credit earnings`""" for job in jobs)
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
                    creditGain = calcCredit(jobs[currentJob]['credits'])
                    unityGain = jobs[currentJob]['unity']

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
                user.setValue('job', value)
                user.addBalance(unity = -10)
                embed = successMsg("Job applied", f"You applied for the job of {value}!\nYou lost 10 Unity during the process.")

        else: embed = errorMsg("Command is not vaild!")

        await message.send(embed=embed)
        self.work.reset_cooldown(message)

