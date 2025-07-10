from discord.ext import commands
from calculatefuncs import *
import asyncio

mkDirNotExist("lottery")

lotteryCost = 10

LOTTERY_INFO = f"""The lottery is a system where you can buy tickets for a chance at winning Credits each day.
Unlike most commands, the lottery system utilizes **3 commands**:
- `{prefix}lottery`: Shows this information. Otherwise, it is useless. (Free Gems?)
- `{prefix}buyticket`: This command takes NO arguments. It allows you to choose 7 numbers to buy a ticket. It will send the ticket ID to the chat, so **make sure you are in a DM if you do not want your ticket being stolen.**
- `{prefix}redeemticket`: Redeem your ticket! Notice: You must redeem it on the day the winning numbers are announced; you will forfeit all rewards if you miss the opportunity. 

__Lottery Information:__
Every time the bot is booted (each day), the bot will send a message in <#{botAIChannel}> announcing the winning numbers.
The numbers are stored on the disk (may change in the future to be generated on the spot).

There are **7** numbers in the lottery. Each number is unique (there cannot be 2 of the same numbers) and is randomly assigned within the range of **1 to 40**.

Buying a ticket costs `{lotteryCost} Credits` (may change), but you can buy an unlimited amount of tickets.
The ticket ID is only valid for the draw number it is registered to, so you cannot use an expired ticket ID to redeem a new one.

**Please redeem the ticket the next day or you will lose all potential rewards!**
Depending on how many numbers you got right, you will gain `Credits`:
1 correct: `{lotteryCost * 0.75} Credits`
2 correct: `{lotteryCost * 2} Credits`
3 correct: `{lotteryCost * 5} Credits`
4 correct: `{lotteryCost * 10} Credits`
5 correct: `{lotteryCost * 50} Credits`
6 correct: `{lotteryCost * 100} Credits`
7 correct: `{lotteryCost * 1000} Credits`
"""
def fname(filename: str) -> str:
    return os.path.join("lottery", filename)

class LotteryIO:
    winsIO = JSONIO(fname("winningNumbers.json"))
    idsIO = JSONIO(fname("ids.json"))
    lotData = JSONIO(fname("lotteryData.json"))

  
    def writeWins(self, winningNumbers: list):
        self.winsIO.writeJSON(winningNumbers)
        self.lotData.writeKey("Draw Number", self.getDrawNum() + 1)

    def getWinningNumbers(self):
        return self.winsIO.readCache()

    def getLotteryID(self, id: str):
        return self.idsIO.readCache().get(id)
    def writeID(self, id: str, numbers: list):
        return self.idsIO.writeKey(id, numbers)
    
    def getDrawNum(self) -> int:
        return self.lotData.readCache().get('Draw Number', 0)

    def getActualID(self, id: str) -> str:
        return str(id) + "|" + str(self.getDrawNum() + 1)

    def ID_exists(self, id: str) -> bool:
        return not self.getLotteryID(str(id) + "|" + str(self.getDrawNum())) is None
    
class Lottery(LotteryIO):
    def generate_numbers(self) -> list[int]:
        """
        Generates a set of winning numbers for the lottery system

        For the lottery system, there are 7 numbers, each with a digit from 1-40.
        Each digit cannot be repeated once.

        """

        # Determine the winning numbers
        digits = list(range(1, 40 + 1))
        winningNumbers = []

        for i in range(7): # Choose 7 numbers
            winningNumber = random.choice(digits)
            winningNumbers.append(winningNumber)
            digits.remove(winningNumber)

        del digits

        # Sort
        winningNumbers.sort()

        # Write to disk
        self.writeWins(winningNumbers)
        return winningNumbers

    def get_credits_amount(self, numbers: list[int]) -> int | float:
        """Returns the amount of Credits to get"""

        # Get winning numbers
        winningNumbers = self.getWinningNumbers()

        # Compare
        matches = 0
        for number in numbers:
            if number in winningNumbers:
                matches += 1

        # Grant Credits
        match matches:
            case 0: return 0
            case 1: return lotteryCost * 0.75
            case 2: return lotteryCost * 2
            case 3: return lotteryCost * 5 
            case 4: return lotteryCost * 10
            case 5: return lotteryCost * 50
            case 6: return lotteryCost * 100
            case 7: return lotteryCost * 1000
            case _: return lotteryCost

    def create_lottery_id(self, numbers) -> int:
        # Generate random ID
        randomID = random.randint(1000000, 9999999)
        id = self.getActualID(randomID)

        # Add on file
        self.writeID(id, numbers)

        # Return ID but not the actual one
        return randomID

lotterySaleUsers = []

class LotteryCog(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.lot = Lottery()

    async def announceWinningNumbers(self):
        # Create new 
        self.lot.generate_numbers()
        
        drawNum = self.lot.getDrawNum()
        winningNumbers = self.lot.getWinningNumbers()

        # Send MSG
        embed = discord.Embed(
            title = f"Lottery Draw #{drawNum} Winning Numbers",
            description = f"The winning numbers this draw are:\n\n" + ", ".join(f"`{i}`" for i in winningNumbers) + f"\n\nIf you have a matching lottery ID, redeem it through `{prefix}redeemticket <lottery ID>`",
            color = 0x00FF00
        )


        # Get channel
        channel = self.bot.get_channel(botAIChannel)
        await channel.send(embed=embed)

     
    @commands.command(
        help = f"Lottery Information",
        description = LOTTERY_INFO,
    )
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def lottery(self, message):
        await message.send(embed=basicMsg(description=LOTTERY_INFO))


    @commands.command(
        help = f"Buy a lottery ticket!\nSpecifying 'random' will generate random lottery numbers",
        aliases = ['buylottery']
    )
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def buyticket(self, message, arg: str = 'none'):
        u = User(message.author.id)

        msg = await message.send(embed=basicMsg(
            "Enter your numbers",
            "Please enter your 7 numbers that you wish to choose seperated by spaces.\nExample: `3 6 8 11 14 23 34`" 
        ))

        try:
            if arg.lower() in ('r', 'random', 'ran', 'gen', 'generate', ' rng'):
                digits = list(range(1, 40 + 1))
                numbers = []

                for i in range(7): # Choose 7 numbers
                    num = random.choice(digits)
                    numbers.append(num)
                    digits.remove(num)

            else:
                ui = await self.bot.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300)
                userInput = ui.content

                numbers = userInput.replace(", "," ").replace(","," ").split(" ")
                
            if len(numbers) == 7:
                # Valid 
                nums = []
                for n in numbers:
                    nums.append(int(n))

                cost = lotteryCost

                # 50% less for FIRST lottery
                if u.ID not in lotterySaleUsers:
                    lotterySaleUsers.append(u.ID)
                    cost /= 2

                # Determine if the user can buy it anyway
                if u.getData("credits") >= cost:
                    u.addBalance(credits = -cost)
                    
                    # Create
                    ticketID = self.lot.create_lottery_id(nums)

                    await msg.edit(embed=successMsg(
                        description=f"Bought a lottery ticket for `{cost} Credits`\nYour numbers are: `{', '.join(str(i) for i in numbers)}`\nTicket ID: `{ticketID}`"
                    ))
                else:
                    await msg.edit(embed=errorMsg(
                        "You do not have enough Credits to buy a ticket!"
                     ))

            else:
                raise ValueError
        except ValueError:
            await msg.edit(embed=errorMsg(
                "You must enter 7 integers seperated by spaces!\nExample: `3 6 8 11 14 15 20`"
            ))
        except (TimeoutError, asyncio.exceptions.TimeoutError):
            await message.send(f"{message.author.mention}, your buyticket after 5 minutes of inactivity!")
    
    
    @commands.command(
        help = f"Redeem a lottery ticket!",
        aliases = ['redeemlottery']
    )
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def redeemticket(self, message, ticketID: str):
        u = User(message.author.id)

        actualID = str(ticketID) + "|" + str(self.lot.getDrawNum())

        if self.lot.ID_exists(ticketID):
            numbers = self.lot.getLotteryID(actualID)

            # Remove
            self.lot.idsIO.deleteKey(actualID)

            credits = self.lot.get_credits_amount(numbers)

            if u.getData('job') == "Gambler":
                credits = round(credits * 1.05, 3)

            u.addBalance(credits)

            await message.send(embed=successMsg(
                description=f"Successfully redeemed ticket!\nYou won `{numStr(credits)} Credits`!"
            ))
        else:
            await message.send(embed=errorMsg(
                f"The ticket ID does not exist, has expired, or is not redeemable right now!"
            ))