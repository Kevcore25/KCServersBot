import discord
from discord.ext import commands
from calculatefuncs import *
import asyncio

class WordleChar:
    letter: str
    position: int

    def __init__(self, letter: str, position: int):
        """
        @param position: An integer from 0-2
        """

        self.position = position
        self.letter = letter.upper()
    
    def __str__(self):
        match self.position:
            case 1:
                return f"*`{self.letter}`*"
            case 2:
                return f"**`{self.letter}`**"
        return f"`{self.letter}`"
    

class WordleGame:
    answer: str
    attempts: int
    data: list[list[WordleChar]]

    def __init__(self):
        # Choose a word
        with open("wordlewords.json", "r") as f:
            words = json.load(f)

        self.answer = random.choice(words)

        self.attempts = 6

        self.data = []

    def guess(self, word: str) -> bool:
        temp = []
        for i in range(5):
            t = word[i]
            a = self.answer[i]

            if t == a:
                temp.append(WordleChar(t, 2))
            elif t in self.answer:
                temp.append(WordleChar(t, 1))
            else:
                temp.append(WordleChar(t, 0))

        self.data.append(temp)

        if word == self.answer:
            return True
        else:
            self.attempts -= 1
            return False

    def determineLose(self) -> bool:
        return self.attempts <= 0

    def getAnswers(self) -> str:
        temp = []
        for word in self.data:
            temp.append(" ".join(str(i) for i in word))
        return "\n".join(temp)
    
dim = DiminishRewards(5, 0.5, 3600)

class WordleGameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(
        help = "Wordle Game",
        description = """A random 5-letter word is chosen from a bank.\nYou have 6 attempts to guess that word.\nIf the letter is in the word, it will be *italicized* and if it is in the same position as the word, it will be **bolded**.\n\nWordle starts giving `5 Credits` but each game decreases the reward (resets 1h after first play).\nGain a bonus +10% earnings for every attempt remaining""",
    )
    async def wordle(self, message: discord.Message):
        u = User(message.author.id)

        dim.add_use(u)

        # Create a new instance of the game
        game = WordleGame()

        def getRwd():
            return round(dim.returnAmount() * (1 + game.attempts / 10), 3)

        # Send init message
        desc = lambda text: f"Type a word! If it is correct, you will earn `{numStr(getRwd())} Credits`.\nAttempts remaining: `{game.attempts}`\n\n{game.getAnswers()}\n\n{text}"
        
        embed = discord.Embed(
            title = "Wordle",
            description = desc(""),
            color = 0xFF00FF
        )
        embed.set_footer(text = "Dictionaries are allowed, but the use of a solver is not allowed")

        msg = await message.send(embed = embed)

        async def edit(text: str): 
            embed = discord.Embed(
                title = "Wordle",
                description = desc(text),
                color = 0xFF00FF
            )
            embed.set_footer(text = "Dictionaries are allowed, but the use of a solver is not allowed")
            await msg.edit(embed = embed)

        # Get words
        with open("5lwords.json", "r") as f:
            words = json.load(f)

        # Get input
        while (not game.determineLose()):
            # Get user input
            try:
                ui = await self.bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300)

                if ui.content.lower() == "exit":
                    await edit("Game exited. Your CD is not reset.") 
                    break

                userInput = ui.content.lower()

                # Check for bounds
                if userInput not in words:
                    await edit(f"`{userInput}` is not a valid 5-letter word!") 
                    continue

                # Guess
                result = game.guess(userInput)

                if result:
                    credits = getRwd()
                    await edit(f"You won! You gained `{numStr(credits)} Credits`")
                    u.addBalance(credits=credits)
                    break

                else:
                    await edit(f"")

            except (TimeoutError, asyncio.exceptions.TimeoutError):
                await message.send(f"{message.author.mention}, your Wordle Game expired after 5 minutes of inactivity!")
                return # Fix potential bug
            except ValueError:
                await edit("Your guess must be an integer!")

        if game.determineLose():
            await edit(f"You lost! I was thinking of `{game.answer}`")