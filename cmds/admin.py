import discord
from discord.ext import commands
from calculatefuncs import *

class AdminCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(
        help = "[ADMIN] Creates a gift code",
        hidden = True
    )
    async def creategift(self, message: discord.Message, amount: str, uses: int = 1, code: str | None = None):
        # Only admins can use this

        # Amount can be a string like 1C 2U or just 1 2U
        # Ex: !creategift 300 (Creates a random gift code with an amount of 300 credits with 1 use)
        # Or: !creategift "5C 2U" 5 ABCDEF (Creates a gift code with an amount of 5 Credits and 2 Unity with 5 uses)
        # Or: !creategift 100,5U 1 ABCDEF (Creates a gift code with an amount of 100 Credits and 5 Unity with 1 use)

        uses = int(uses)

        if message.author.id in adminUsers:
            # Gen a code
            if code is None:
                code = ''.join(random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]).upper() for i in range(8))

            # Get amounts

            credits = 0
            unity = 0
            gems = 0

            amount = amount.replace(" ", ",").lower()

            tempint = []
            for amt in amount.split(","):
                for t in amt:
                    if t.isdigit() or t in ['.', '-']:
                        tempint.append(t)
                    else:
                        adding = float("".join(tempint))
                        match t:
                            case "c": 
                                credits += adding
                            case "u":
                                unity += adding
                            case "g":
                                gems += adding
                        tempint = []
                        break # Break out of this so the next values can be entered
            
            # Save gift code
            try:
                with open("giftcodes.json", "r") as f:
                    codes = json.load(f)
            except FileNotFoundError:
                with open('giftcodes.json', 'w') as f:
                    f.write("{}")
                codes = {}

            codes[code] = [credits, unity, gems, uses]

            with open('giftcodes.json', 'w') as f:
                json.dump(codes, f, indent=4)

            # Send MSG
            await message.send(f"Created a gift code of: `{code}` giving the following: `{credits} Credits`, `{unity} Unity`, and `{gems} Gems`")
        else:
            await message.send("You are not permitted to use this command!")
