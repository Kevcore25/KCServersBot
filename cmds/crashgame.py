import discord
from discord.ext import commands
from calculatefuncs import *
import matplotlib.pyplot as plt
from games import CrashGame
from scipy.interpolate import make_interp_spline
import asyncio
import numpy as np

class CrashGameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        help = f"Play the crash game!",
        description = """This version is modified and split into "rounds" which take about 1 second to update. Each turn has a chance of crashing.\nYou lose `1 Unity` for playing but gain `1 Unity` for cashing out.""",
        aliases = ['cg', 'crash']
    )
    @commands.cooldown(1, 300, commands.BucketType.user) 
    async def crashgame(self, message: discord.Message, betAmount: float = None, autoCash: float = "0"):
        user = User(message.author.id)

        with open("previousCgs.json",'r') as f:
            previousCgs = json.load(f)  
            
        if betAmount is None:
            plt.xlabel("Game Number")
            plt.ylabel("Ended Multiplier")
            plt.plot(
                range(len(previousCgs)),
                previousCgs
            )
            plt.savefig('temp/cgt.png')
            plt.clf()
            file = discord.File(f"temp/cgt.png", filename=f"cgt.png")
            embed = discord.Embed(
                title = "Previous Multipliers",
                color = 0xFF00FF, 
                description=", ".join(
                    (str(round(i, 2))+"x" if i < 5 else (
                        "**"+str(round(i, 2))+"x**" if i < 16 else "***"+str(round(i, 2))+"x***"
                    )) for i in previousCgs[-100:] 
                ) + \
                f"\nTotal average: {round(sum(previousCgs) / len(previousCgs), 2)}x multiplier" + \
                f"\nAverage of last 100: {round(sum(previousCgs[-100:]) / len(previousCgs[-100:]), 2)}x multiplier"
            )        
            embed.set_image(url=f"attachment://cgt.png")

            await message.send(file=file, embed=embed)
            self.crashgame.reset_cooldown(message)
            return
    
        betAmount = round(float(betAmount), 2)
        autoCash = float(autoCash)
        
        if betAmount < 0 or betAmount > user.getData('credits'):
            await message.send(embed=discord.Embed(description="Invalid bet amount!", color=0xFF0000))
            self.crashgame.reset_cooldown(message)
            return
        if betAmount > 10000:
            await message.send(embed=discord.Embed(description="A maxmium of 10k Credits can be betted!", color=0xFF0000))
            self.crashgame.reset_cooldown(message)
            return
        user.addBalance(credits=-betAmount, unity = -1)

        msg = await message.send(embed=discord.Embed(
            title="Starting...",
            description="Please wait while I set up the game...",
            color = 0xFF00FF,
        ))
        randomNum = random.randint(0,999999)

        cg = CrashGame()

        cashedOut = False

        #plot = cg.create_plot()
        
        xpoints = [0]
        ypoints = [1]
        await msg.add_reaction("💰")
        await msg.add_reaction("🛑")

        def check(reaction, user):
            return user == message.author and (str(reaction.emoji) == '💰' or str(reaction.emoji) == '🛑')
        async def cgupdate():
            file = discord.File(f"temp/cg{randomNum}.png", filename=f"cg{randomNum}.png")
            embed = discord.Embed(title = f"Crash Game",color = 0xFF00FF, description="""Press the cash emoji (💰) to cash out.\nPress the stop emoji (🛑) to cash out and/or stop the game.""")        
            embed.set_image(url=f"attachment://cg{randomNum}.png")
            embed.set_footer(text="The only game you can earn so much?!")

            await msg.edit(attachments=[file], embed=embed)

        def p(x = xpoints, y = ypoints, color="b"):
            # create integers from strings
            plt.xlabel("Round")
            plt.ylabel("Multiplier")

            try:
                idx = range(len(x))
                xnew = np.linspace(min(idx), max(idx), 300)

                # interpolation
                spl = make_interp_spline(idx, y, k=2)
                smooth = spl(xnew)

                # plotting, and tick replacement
                plt.plot(xnew, smooth, color)
            except ValueError:
                plt.plot(x,y, color)

            plt.savefig(f"temp/cg{randomNum}.png")
            plt.clf()

        # If the user pressed the stop button, then the game should speed up to its final multiplier
        stopped = False

        while True:
            try:
                if not stopped:
                    userMsg = await self.bot.wait_for('reaction_add', timeout=1.5, check=check)

            except (TimeoutError, asyncio.exceptions.TimeoutError):
                pass
            else:
                if not cashedOut:
                    
                    won = cg.cash_out(betAmount)
                    user.addBalance(credits=won, unity=1)
                    cashedOut = True

                    await message.send(f"Won `{won} Credits`! (Actual gained: `{numStr(won - betAmount)} Credits`)")

                if str(userMsg[0].emoji) == "🛑":
                    # plt.title(f"Round {cg.round} | Multiplier: {r['multiplier']}x (Stopped by user)")
                    p()
                    stopped = True
                    # await cgupdate()
            
            
            r = cg.next_round()

            if autoCash <= float(r['multiplier']) and not cashedOut and autoCash != 0:
                won = cg.cash_out(betAmount)
                user.addBalance(credits=won)
                cashedOut = True

                await message.send(f"Won {won}! (Autocashed)")             

            if r['crashed']:

                # Precog
                if user.get_item("Precognition") and not cashedOut:
                    won = cg.cash_out(betAmount)
                    user.addBalance(credits=won)
                    cashedOut = True

                    await message.send(f"**Precognition**: Won `{won} Credits`! (Actual gained: `{numStr(won - betAmount)} Credits`)")             

                    if user.ID != "main": 
                        user.delete_item("Precognition")

                plt.title(f"Round {cg.round} | Multiplier: {r['multiplier']}x (CRASHED!)")

                xpoints.append(cg.round)
                ypoints.append(0)

                p(color='r')

                await cgupdate()

                break


            xpoints.append(cg.round)
            ypoints.append(r['multiplier'])

            if not stopped:
                plt.title(f"Round {cg.round} | Multiplier: {r['multiplier']}x")

                p(xpoints, ypoints)

                if not stopped:
                    await cgupdate()
                
        os.remove(f"temp/cg{randomNum}.png")
        self.crashgame.reset_cooldown(message)

        previousCgs.append(r['multiplier'])
        with open("previousCgs.json",'w') as f:
            json.dump(previousCgs, f)