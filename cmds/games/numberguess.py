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
                await message.send(f"{message.author.mention}, your RNG Guessing Game expired after 5 minutes of inactivity!")
                return # Fix potential bug
            except ValueError:
                await edit("Your guess must be an integer!")

        if game.determineLose():
            await edit(f"You lost! I was thinking of `{game.answer}`")

    @commands.command(
        help = "RNG Guessing Survery",
        description = """Complete a survey pertaining to the RNG Guessing Game to earn Unity!\nReminder: Unity converts into Credits automatically when you hit maximum Unity!\n"""+ """
Purpose: Ask the user for their opinion on whether a number is a warm, cold, or hot in different scenarios.
After a bunch of data collection, this is then fed into an analysis for the actual RNG Guessing Game.

The survey consists of 2 random values within the accepted ranges. One of which is the actual answer and the other is the guess.
The user asks whether it is hot, warm, or cold. 

Accepted ranges are either:
1. 1-10
2. 1-20
3. 1-30
4: 1-40
In other definitions, it is (1 to (10 * randint(1, 4)))
""",
        aliases = ["rngsurvey", "rngs", "survey"]
    )
    @commands.cooldown(20, 3600, commands.BucketType.user)
    @commands.cooldown(100, 3600, commands.BucketType.channel)
    async def rnggamesurvey(self, message: discord.Message):
        u = User(message.author.id)

        for i in range(100):
                # Get range
                rmax = 10 * random.randint(1, 4)

                # Guess number
                guessNumber = random.randint(1, rmax)

                # Answer
                answer = random.randint(1, rmax)
                
                # Regenerate if it is too close
                if abs(answer - guessNumber) > 1:
                    break

        # Ask user
        await message.send(embed = basicMsg(
            "RNG survey",
            "Please determine your choice of a hint for the following RNG Game.\nReply with either `hot`, `warm`, or `cold`.\nPlease be sincere with your answer; your survey is collected to improve the RNG Guessing Game hints\nFor participating in this survey, you will gain `+0.5 Unity` and you can do this survey up to 20 times every hour.\n\n" + \
                f"In a game with a range of `1 to {rmax}`, choose what hint to give if:\n" + \
                f"The answer is `{answer}`,\nand the guess is `{guessNumber}`" 
        ))
        try:
            msg = await self.bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300)

            ui = msg.content.lower()

            if ui == "exit":
                await message.send("Survey Exited.") 
            elif ui in ['hot', 'cold', 'warm']:
                # Determine if file exists
                if not os.path.exists("rngsurvey.json"):
                    with open('rngsurvey.json', 'x') as f:
                        f.write("[]")

                with open('rngsurvey.json', 'r') as f:
                    data: list = json.load(f)
                
                data.append(
                    [rmax, guessNumber, answer, ui]
                )
                
                with open('rngsurvey.json', 'w') as f:
                    json.dump(data, f)

                u.addBalance(unity = 0.5)

                await message.send(embed= successMsg(
                    description = "Thank you for participating in this survey!\nYou gained `+0.5 Unity`!\nDo more if interested!"
                )) 
            else:
                await message.send(embed = errorMsg(
                    "Not a valid hint!"
                ))
        except (TimeoutError, asyncio.exceptions.TimeoutError):
            await message.send(f"{message.author.mention}, your survey expired after 5 minutes of inactivity!")
            return # Fix potential bug
