import discord
from discord.ext import commands
from calculatefuncs import *
import asyncio

ESCAPE = ''

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
                return f"[2;33m[1;33m{self.letter}"
            case 2:
                return f"[2;33m[1;32m{self.letter}"

        return f"[0m{self.letter}"
    

class WordleGame:
    answer: str
    attempts: int
    word_data: list[list[WordleChar]]

    def __init__(self):
        # Choose a word
        with open("wordlewords.json", "r") as f:
            words = json.load(f)

        self.answer = random.choice(words)

        self.attempts = 6

        self.word_data = []

    def guess(self, word: str) -> bool:
        feedback = [WordleChar(t, 0) for t in word]
        answer_used = [False] * len(self.answer)
        
        # Correct pos
        for i in range(len(word)):
            if word[i] == self.answer[i]:
                feedback[i] = WordleChar(word[i], 2)
                answer_used[i] = True

        # In word but not correct
        for i in range(len(word)):
            if feedback[i].position == 0: 
                for j in range(len(self.answer)):
                    if not answer_used[j] and word[i] == self.answer[j]:
                        feedback[i] = WordleChar(word[i], 1)
                        answer_used[j] = True 
                        break

        self.word_data.append(feedback)

        if word == self.answer:
            return True
        else:
            self.attempts -= 1
            return False

    def determineLose(self) -> bool:
        return self.attempts <= 0

    def getAnswers(self) -> str:
        temp = []
        for word in self.word_data:
            temp.append(" ".join(str(i) for i in word))

        # Don't display ANSI if none
        if len(temp) == 0:
            return "``` ```"
        else:
            return "```ansi\n" + "\n".join(temp) + "```"
    
    def returnKeyboard(self):
        keyboard = (
            'Q W E R T Y U I O P',
            ' A S D F G H J K L',
            '  Z X C V B N M'
        )

        newKeyboard = []

        for kbRow in keyboard:
            newRow = []

            for key in kbRow:
                if key == ' ': 
                    newRow.append(' ')
                    continue
                
                highest = -1

                # Iterate through all the wordle data 
                for row in self.word_data:
                    for wchar in row:
                        if wchar.letter.upper() == key:
                            highest = max(highest, wchar.position)

                match highest:
                    case -1:
                        newRow.append('[2;0m' + key)
                    case 0:
                        newRow.append('[2;30m' + key)
                    case 1:
                        newRow.append('[2;33m' + key)
                    case 2:
                        newRow.append('[2;32m' + key)

            newKeyboard.append(''.join(newRow))

        return '\n'.join(newKeyboard)

dim = DiminishRewards(10, 1, 3600)
firstWordles = []


class WordleGameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        


    @commands.command(
        help = "Wordle Game",
        description = """A random 5-letter word is chosen from a bank.\nYou have 6 attempts to guess that word.\nIf the letter is in the word, it will be *italicized* and if it is in the same position as the word, it will be **bolded**.\n\nWordle starts giving `5 Credits` but each game decreases the reward (resets 1h after first play).\nGain a bonus +10% earnings for every attempt remaining.\nThe first wordle each day will grant 2x more Credit rewards.\n\nYou are not allowed to use a wordle solver or AI or any unfair advantage, but you are able to use the dictionary.\nAnyone recognized using a solver will be subjected to a 75% earnings lost; however, they will still be able to play.""",
    )
    async def wordle(self, message: discord.Message):
        global firstWordles

        u = User(message.author.id)

        dim.add_use(u)

        # Create a new instance of the game
        game = WordleGame()

        # New Hint mode
        hint = ''

        def getRwd():
            credits = round(dim.returnAmount(u) * (1 + game.attempts / 10), 3)
            if message.author.id not in firstWordles:
                credits *= 2
            return credits
        
        def desc(text: str):
            if hint != '':
                return f"Type a word! If it is correct, you will earn `{numStr(getRwd())} Credits`.\nAttempts remaining: `{game.attempts}`\nHint: `{hint}` {game.getAnswers()}```ansi\n{game.returnKeyboard()}```{text}"
            else:
                return f"Type a word! If it is correct, you will earn `{numStr(getRwd())} Credits`.\nAttempts remaining: `{game.attempts}` {game.getAnswers()}\n```ansi\n{game.returnKeyboard()}```{text}"
            
        # Send init message
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
                userInput = ui.content.lower()

                # Check if it is 5 length
                if len(userInput) != 5:
                    continue

                if userInput == "exit":
                    await edit(f"Game exited. Your CD is not reset.\nThe word was `{game.answer}`") 
                    break

                if userInput == "hint":
                    if hint != '':
                        await edit(f'You already used a hint!')
                    elif game.attempts == 1:
                        await edit(f"You can't use the hint in your last attempt")
                    else:
                        hint = random.choice(game.answer)
                        game.attempts -= 1
                        await edit(f"Hint used. A random letter in the word is now shown.")
                    continue

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

        firstWordles.append(message.author.id)