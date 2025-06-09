import discord
from discord.ext import commands
from calculatefuncs import *
import asyncio

class RNGNumberGame: 
    min: int
    max: int
    attempts: int
    rewardMulitplier: float
    answer: int
    
    baseReward: float = 1 # Base reward for guessing the number correctly

    warmThreshold: float = 0.25 
    hotThreshold: float = 0.1

    def __init__(self, difficulty: str): 
        match difficulty.lower():
            case "easy":
                self.min = 1
                self.max = 10
                self.attempts = 7
                self.rewardMultiplier = 1
            case "medium" | "normal":
                self.min = 1
                self.max = 20
                self.attempts = 5
                self.rewardMultiplier = 2.5
            case "hard":
                self.min = 1
                self.max = 30
                self.attempts = 5
                self.rewardMultiplier = 5
            case "extreme" | "insane":
                self.min = 1
                self.max = 40
                self.attempts = 4
                self.rewardMultiplier = 10
            case "impossible":
                self.min = 0
                self.max = 10000
                self.attempts = 1
                self.rewardMultiplier = 1000

        self.generateNumber()

    def generateNumber(self):
        self.answer = random.randint(self.min, self.max)

    def guess(self, number: int) -> bool:
        if number == self.answer:
            return True
        else:
            self.attempts -= 1    
            return False

    def determineLose(self) -> bool:
        return self.attempts <= 0
    
    def getReward(self) -> float:
        # Also give bonus based on attempts, with formula: Amount * (1 + Attempts/10)
        return round(self.baseReward * self.rewardMultiplier * (1 + self.attempts/10), 3)
    
    def hint(self, number: int) -> str:
        # Check if the number is warm or hot

        if number > self.answer * (1 - self.hotThreshold) - 1 and number < self.answer / (1 - self.hotThreshold) + 1:
            return "Hot"        
        elif number > self.answer * (1 - self.warmThreshold) - 2 and number < self.answer / (1 - self.warmThreshold) + 2:
            return "Warm"
        else:
            return "Cold"
        

class RNGNumberGuessCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    

    @commands.command(
        help = "RNG Guessing Game",
        description = """Choose a difficulty! Options are easy, medium, hard, and extreme.\nYou will have certain attempts to guess the number. If you are correct, you will earn Credits based on the difficulty you selected\nEarn bonus Credits by having more attempts.\nPlaying this game is **free** but you can only play it once every hour.\n-# This game can either be played by starting off risky (being right = higher win chance) or safer (using a modified *binary search* method for most consistency)""",
        aliases = ["rnggg", "rng", "guessinggame", "gg"]
    )
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def rngguessinggame(self, message: discord.Message, difficulty: str = "normal"):
        u = User(message.author.id)

        # Create a new instance of the game
        game = RNGNumberGame(difficulty)

        def getRwd():
            return calcCredit(game.getReward(), u)

        # Send init message
        desc = lambda text: f"Type a number! If it is correct, you will earn `{getRwd()} Credits`.\nThe number I am thinking of is between `{game.min}` and `{game.max}`\nAttempts remaining: `{game.attempts}`\n\n{text}"

        msg = await message.send(embed = discord.Embed(
            title = "RNG Guessing Game",
            description = desc(""),
            color=0xFF00FF
        ))

        async def edit(text: str): 
            await msg.edit(embed = discord.Embed(
                title = "RNG Guessing Game",
                description = desc(text),
                color = 0xFF00FF
            ))

        # Get input
        while (not game.determineLose()):
            # Get user input
            try:
                ui = await self.bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300)

                if ui.content.lower() == "exit":
                    await edit("Game exited. Your CD is not reset.") 
                    break

                userInput = int(ui.content)

                # Check for bounds
                if not (userInput >= game.min and userInput <= game.max):
                    await edit("Your guess must be within the boundaries!") 
                    continue

                # Guess
                result = game.guess(userInput)

                if result:
                    credits = getRwd()
                    await edit(f"You won! You gained `{numStr(credits)} Credits`")
                    u.addBalance(credits=credits)
                    break

                else:
                    await edit(f"Your guess of `{userInput}` was `{game.hint(userInput)}`")

            except (TimeoutError, asyncio.exceptions.TimeoutError):
                message.send(f"{message.author.mention}, your RNG Guessing Game expired after 5 minutes of inactivity!")
                return # Fix potential bug
            except ValueError:
                await edit("Your guess must be an integer!")

        if game.determineLose():
            await edit(f"You lost! I was thinking of `{game.answer}`")