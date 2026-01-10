import discord
from discord.ext import commands
from calculatefuncs import *
import asyncio 

class NumberMemoryGame(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        

    @commands.command(
        help = f"See if you can remember numbers!",
        description = """For 5 rounds, 6-digit numbers will be displayed for a few seconds. Your goal is to remember the number correctly, 5 times.\nI made this to train on remembering those fricking verification codes.\n\nReward: `5 Credits` per correct round + bonus `1 Unity` for all 5 correct."""
    )
    @commands.cooldown(1, 300, commands.BucketType.user) 
    async def codetest(self, message: discord.ext.commands.Context):
        user = User(message.author.id)

        embed = discord.Embed(
            title = "Verification Code Test",
            description="""This is a game, where you have to **correctly remember the 6-digit code**.\nThere are **5 rounds**.\nEach successful guess grants `5 Credits`, and you will get a bonus `1 Unity` if all rounds are correct.\n\n**This game will start in approximately 5 seconds.**\n\nTry not to type/copy the answer - the point of the game is to train for remembering verification codes!""",
            color=0xFF00FF
        )
        msg = await message.send(embed=embed)

        # set vars
        correct = 0

        await asyncio.sleep(5)

        for round in range(1, 6):
            # Generate number
            number = f"{random.randint(100000, 999999):06}"

            # Send msg for a few sec
            embed.description = f"**Round: {round}/5**\n-# Correct: {correct}/5\n\n**Code: `{number}`**"
            await msg.edit(embed=embed)
            await asyncio.sleep(2.875 - (3/8 * round))

            embed.description = f"**Round: {round}/5**\n-# Correct: {correct}/5\n\n**What was the code? Send the code in the channel.**"
            await msg.edit(embed=embed)


            # Ask for user input

            for i in range(10):
                try:
                    ui = await self.bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300)
                    userInput = ui.content
                except (TimeoutError, asyncio.exceptions.TimeoutError):
                    await message.send(f"{message.author.mention}, your guessing game expired after 5 minutes of inactivity!")
                    return # Fix potential bug


                if len(userInput) == 6 and userInput.isdigit():
                    # Delete if possible
                    try:
                        await ui.delete()
                    except discord.errors.Forbidden:
                        pass

                    break
            else:
                userInput = "XXXXXX"


            if str(userInput).strip() == str(number).strip():
                correct += 1
                embed.description = f"**Round: {round}/5**\n-# Correct: {correct}/5\n\n**Correct! The code was `{number}`**"
                s = 1
            else:
                embed.description = f"**Round: {round}/5**\n-# Correct: {correct}/5\n\n**Incorrect! The code was `{number}` (you answered `{userInput}`)**"
                s = 2

            await msg.edit(embed=embed)
            await asyncio.sleep(s)


        credits = correct * 5
        unity = int(correct == 5) # True is also 1 soo

        # Give
        user.addBalance(credits=credits, unity=unity)

        embed.description = f"The game is over!\n\nYou got {correct} out of 5 rounds correct.\n\nYou earned `{credits} Credits` and `{unity} Unity`"
        await msg.edit(embed=embed)