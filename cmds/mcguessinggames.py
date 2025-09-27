import discord
from discord.ext import commands
from calculatefuncs import *
import requests, threading, asyncio

# Pull MCHangman data from an official source so it is updated once a in while
def pull_mch_data():
    """Pulls data from the MC Property Encyclopedia"""

    # Entity data
    entityData = requests.get("https://joakimthorsen.github.io/MCPropertyEncyclopedia/data/entity_data.json").json().get('key_list')
    # Block data
    blockrawdata = requests.get("https://joakimthorsen.github.io/MCPropertyEncyclopedia/data/block_data.json").json()
    blockData = blockrawdata.get('key_list')
    # Item data
    itemData = requests.get("https://joakimthorsen.github.io/MCPropertyEncyclopedia/data/item_data.json").json().get('key_list')

    # All data
    data = entityData + blockData + itemData

    # Write to file
    with open('mcdata.txt', 'w') as f:
        f.write(
            '\n'.join(data)
        )

    # Also pull for the MCPropertyGuesser game
    with open("mcpgdata.json", 'w') as f:
        json.dump(blockrawdata, f)

# Put in a thread to prevent code stalling
threading.Thread(target=pull_mch_data).start()

dim = DiminishRewards(initialReward=5, minimumReward=0.5, reset=3600)

class MCGuessingGames(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
            


    @commands.command(
        help = f"Play a simliar version of Hangman",
        description = """A random word will be chosen from a bank. You will have letter attempts and guess attempts. Say a letter to guess a letter, and anything else to guess the word.\n-# *Data sourced from the [MC Property Encyclopedia](https://joakimthorsen.github.io/MCPropertyEncyclopedia/)*\n\nReward: `5 * attempts` Credits (diminishes over 1h, `minimum 0.5 * attempts`)""",
        aliases = ['mch', 'minecrafthangman']
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def mchangman(self, message: Context):
        u = User(message.author.id)

        dim.add_use(u)

        # Get data
        with open("mcdata.txt", 'r') as f:
            content = f.read()
        # Parse
        items = []
        for ln in content.splitlines():
            ln = ln.replace("[JE]",'').replace("[BE]",'')
            for i in ("+","-","(","["):
                if i in ln:
                    break
            else:
                items.append(ln.strip().lower())

        # Pick a random item
        item: str = random.choice(items)
        item = item#.strip().lower()
        

        # Scramble
        scrambled = []

        guessed = []

        # Attempts and guesses
        attempts = 6 # round(5 + len(item.replace(" ",'')) ** 0.5)
        guesses = 5


        # if 2 + len(set(tuple(item))) < attempts:
        #     attempts = 2 + len(set(tuple(item)))


        for i in item:
            if i == " ": scrambled.append( " ")
            else: scrambled.append("_")

        # Credit formula.
        cred = lambda: round(dim.returnAmount(u) * attempts, 3)

        # Send MSG
        msg = await message.send(embed=discord.Embed(
            title = "Minecraft Guessing Game",
            description = f"""A random word was chosen from a [bank](https://joakimthorsen.github.io/MCPropertyEncyclopedia/). Say a letter to guess a letter. Type the full word to win.
At anytime in the game, type `exit` to exit out of the game.
Winning will give you `{numStr(cred())} Credits`.

**`{' '.join(i for i in scrambled)}`**

Attempts left: `{attempts}`
Word Guesses left: `{guesses}`

Guessed: `{', '.join(guessed if len(guessed) > 0 else (' ',))}`
-# *There is {len(items)} items that the game can choose from*
            """,
            color=0xFF00FF

        ))

        async def edit(text: str):
            await msg.edit(embed=discord.Embed(
                title = "Minecraft Guessing Game",
                description = f"""A random word was chosen from a [bank](https://joakimthorsen.github.io/MCPropertyEncyclopedia/). Say a letter to guess a letter. Type the full word to win.
At anytime in the game, type `exit` to exit out of the game.
Winning will give you `{cred()} Credits`.

**`{' '.join(i for i in scrambled)}`**

Letter Attempts left: `{attempts}`
Word Guesses left: `{guesses}`

Guessed: `{', '.join(guessed)}`
{text}""",
                color=0xFF00FF
            ))
        while True:
            try:
                ui = await self.bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300)
                userInput = ui.content
            except (TimeoutError, asyncio.exceptions.TimeoutError):
                await message.send(f"{message.author.mention}, your MC hangman expired after 5 minutes of inactivity!")
                return # Fix potential bug
            userInput = str(userInput).lower()

            # Exit
            if userInput == "exit":
                await edit(f"*Exited MCHangman game.*") # Makes it BOLD, not italtic
                return
            
            # Already did before
            if userInput in guessed:
                await edit(f"*You already guessed that letter!*") # Makes it BOLD, not italtic

            # Letter guess
            elif len(userInput) == 1:             
                guessed.append(userInput)
                attempts -= 1

                if userInput in item:
                    for i in range(len(item)):
                        if item[i] == userInput:
                            scrambled[i] = userInput
    
                    await edit(f"*`{userInput}` is in the word!*")

                    if "_" not in scrambled:
                        c = cred()
                        
                        u.addBalance(c)
                        await edit(f"**You won! You gained `{numStr(c)} Credits`!**") # Makes it BOLD, not italtic
                        return
                        
                else:
                    await edit(f"*`{userInput}` is not in the word!*")

                if attempts <= 0:
                    await edit(f"**You lost! You ran out of attempts! The word was `{item.title()}`**")
                    return
            elif userInput == item:            

                c = cred()
                guesses -= 1 #No cred penalty but minus 1 to the counter for edit

                u.addBalance(c)
            
                await edit(f"*You won! You gained `{numStr(c)} Credits`!*") # Makes it BOLD, not italtic
                self.mchangman.reset_cooldown(message)
                return
            # Guess wrong
            elif userInput in items:
                guesses -= 1

                if guesses == 0:
                    await edit(f"**You lost! You ran out of word guesses! The word was `{item.title()}`**")
                    return
                else:
                    await edit(f"*`{userInput.title()}` is not the word!*")
            else:
                continue # Continue the loop
            
            try:
                # One of the if statements ran, so delete author msg
                await ui.delete()
            except discord.errors.Forbidden:
                pass

    @commands.command(
        help = f"MCPG dictionary",
        description = f"""Format: {prefix}mcd <dictionary>""",
        aliases = ['mcd']
    )
    async def mcpgdictionary(message: discord.Message, property: str):    
        
        with open("mcpgdata.json", 'r') as f:
            mcpgdata = json.load(f)

        for i in mcpgdata['properties']:
            if mcpgdata['properties'][i]['property_name'].lower() == property:
                try:
                    await message.send(mcpgdata['properties'][i]['property_description'])
                except KeyError:
                    await message.send("The property has no description 🤷 lol")
                break
        else:
            await message.send("property does not exist")

    @commands.command(
        help = f"Play a block property guesser (BETA)",
        description = """A random word will be chosen from a bank. You will have hints and guess attempts to try to guess the block the bot was thinking.\n-# *Data sourced from the [MC Property Encyclopedia](https://joakimthorsen.github.io/MCPropertyEncyclopedia/)*""",
        aliases = ['mcg', 'mcpg', 'mcp']
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def mcpropertyguesser(self, message: discord.Message):    
        u = User(message.author.id)
        
        with open("mcpgdata.json", 'r') as f:
            mcpgdata = json.load(f)
        # First of all, Choose the WORD
        items = []
        itemslower = []
        for ln in mcpgdata['key_list']:
            for i in ("+","-","(","["):
                if i in ln:
                    break
            else:
                items.append(ln.strip())
                itemslower.append(ln.strip().lower())

        block: str = random.choice(items)
        properties = list(mcpgdata['properties'])

        # Remove "tag" properties
        blacklist = ["tag", "face", "collision", "map_color", 'id', 'pathfinding', "placement", "()"]
        for p in properties.copy():
            for blacklisted in blacklist:
                if blacklisted in p:
                    try:
                        properties.remove(p)
                    except ValueError: pass
        # Now, shuffle the properites. This will be in the order of the hints
        random.shuffle(properties)

        # Now, make a "link" to the properties of the block.
        def get_property(property: str) -> dict[str, str]:
            """Returns into a dict of format:
            {
                name: str (name of property)
                value: str (the value of the property)
            }
            """

            # Link - easier to code
            p = mcpgdata['properties'][property]

            name = p['property_name']

            # Value:
            if block in p['entries']:
                value = p['entries'][block]
                # if dict, means multiple states so combine it into sentences
                if isinstance(value, dict):
                    tempstr = []
                    for k, v in value.items():
                        tempstr.append(f"{k}: {v}")
                    value = ". ".join(tempstr) 
                elif "not updated to" in value.lower() and "(" in value:
                    value = value.split("(")[0]
            else:
                value = p['default_value']
            # remove the bracket if it is something like not updated...
        
            
                
            return {"name": name, "value": value}
        
        # Set values
        hints = len(properties) - 10

        # Can choose to use hints but nah this is safer
        currentPropertyIndex = 5

        guesses = 10
        guessed = []

        # Return the properties in string (markdown) format
        def get_current_properties():
            tempstr = []
            for i in range(currentPropertyIndex):
                p = get_property(properties[i])

                tempstr.append(f"**{p['name']}**: {p['value']}")

            return "\n".join(tempstr)
        
        # At this point, most of the code is done so just send msg
        msg = await message.send(embed=discord.Embed(
            title = "Minecraft Block Property Guessing Game",
            description = f"""A random word was chosen from a [bank](https://joakimthorsen.github.io/MCPropertyEncyclopedia/). Say `hint` to get the next property, say `exit` to exit out of this game, or say the name of the block to guess it.

Block Properties:
{get_current_properties()}

Hints left: `{hints}`
Guesses left: `{guesses}`

Guessed: `{', '.join(guessed if len(guessed) > 0 else (' ',))}`
            """,
            color=0xFF00FF
        ))

        async def edit(text: str):
            await msg.edit(embed=discord.Embed(
                title = "Minecraft Block Property Guessing Game",
                description = f"""A random word was chosen from a [bank](https://joakimthorsen.github.io/MCPropertyEncyclopedia/). Say `hint` to get the next property, say `exit` to exit out of this game, or say the name of the block to guess it.

Block Properties:
{get_current_properties()}

Hints left: `{hints}`
Guesses left: `{guesses}`

Guessed: `{', '.join(guessed if len(guessed) > 0 else (' ',))}`

{text}""",
            color=0xFF00FF
            ))
        while True:
            try:
                ui = await self.bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300)
                userInput = ui.content
            except (TimeoutError, asyncio.exceptions.TimeoutError):
                message.send(f"{message.author.mention}, your mc property guesser expired after 5 minutes of inactivity!")
                return # Fix potential bug
            
            userInput = str(userInput).lower()

            # Exit
            if userInput == "exit":
                await edit(f"Exited MC Property Guesser game. The block was `{block}`") # Makes it BOLD, not italtic
                return
            
            # Already did before
            if userInput in guessed:
                await edit(f"You already guessed that block!") # Makes it BOLD, not italtic

            # hint
            elif userInput == 'hint':             

                if hints > 0:
                    hints -= 1
                    currentPropertyIndex += 1

                    await edit('A property was revealed!')
            
                else:
                    await edit(f"You ran out of hints! Guess the block or say `exit` to exit the game.")

            
            elif userInput == block.lower():            

                c = calcCredit(10 + (hints / 2), u)
                guesses -= 1 # minus 1 to the counter for edit
            
                # add money
                u.addBalance(credits=c)

                await edit(f"*You won! You gained `{numStr(c)} Credits`!*") # Makes it BOLD, not italtic
                self.mcpropertyguesser.reset_cooldown(message)
                return
            
            # Guess wrong
            elif userInput in itemslower:
                guesses -= 1
                guessed.append(userInput)

                if guesses == 0:
                    await edit(f"*You lost! You ran out of guesses! The block was `{block.title()}`*")
                    return
                else:
                    await edit(f"`{userInput.title()}` is not the word!")

            else: continue # Continue the loop

            # One of the if statements ran, so delete author msg
            await ui.delete()

