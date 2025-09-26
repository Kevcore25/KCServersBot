import discord
from discord.ext import commands
from calculatefuncs import *

LOAN_DESC = f'''You can loan up to a certain amount of Credits in order to help you become richer!
By default, you may only loan up to a value of 50% of your Score. 
Having at least 75 Unity will bump it to 75% of your Score.
As score generally starts linear and slows during late-game, this usually is a good number of how much you can loan up to.
Score depends on many factors, so negative Unity for example would cause lower scores as well.

After loaning an amount of Credits, you must pay an interest within 1 week, or you will suffer Unity losses.
The interest is randomized from 10% to 20%, and the Unity loss depends on how much you had loaned:
* For less than 1k loaned: -50 Unity
* For 1k loaned and over: -100 Unity

You must pay off your loan debt before being able to loan again.
If you fail to pay your loan before a reset, you will lose -25 Unity following the reset, negatively impacting your early-game start and thus your score.

During your loan period, you can spend your Credits on whatever you like, whether it is gambling, investing, or buying items from the shop.
However, you are unable to use the KCash exchange service while you are on a loan though the Gem exchange still works.
'''

class LoanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(
        help = 'Loan Credits from the bot!',
        description = LOAN_DESC
    )
    async def loan(self, message: Context, value: str = None):
        u = User(message.author.id)
        
        # Get max loan amount
        if u.getData('unity') >= 75:
            maxLoan = round(calcScore(u) * 0.75)
        else:
            maxLoan = round(calcScore(u) / 2)

        if value is None:
            await message.send(embed = basicMsg(
                "Loaning Information",
                f"You can loan up to `{maxLoan:>,} Credits`.\nYou must pay 15% ±5% interest within 1 week of your loan or before a reset.\nOtherwise, you will suffer Unity losses.\n\nHow to use:\n{prefix}loan <amount> - Loan an amoutn of credits\n{prefix}loan repay - Repay your loan\n\nRun the help command on this command for more loaning information."
            ))
        elif value.lower() == "repay":
            loan = u.getData('loan')
            if loan['amount'] == 0:
                return await message.send(embed=errorMsg(
                    f"You don't have a loan right now!"
                ))

            amount = round(loan['amount'] * (1 + loan['interest']), 2)

            if u.getData("credits") >= amount:
                # Reset values
                loan['amount'] = loan['interest'] = loan['expires'] = 0

                u.addBalance(credits = -amount)
                u.setValue('loan', loan)

                await message.send(embed=successMsg(
                    description = f"You successfully repaid your loan for `{amount} Credits`!"
                ))

            else:
                await message.send(embed=errorMsg(
                    f"You must have at least `{numStr(amount)} Credits` in order to repay your loan!"
                ))

        elif value.isdigit():
            value = int(value)

            if value <= 0:
                return await message.send(embed=errorMsg(
                    "Value cannot be under 0!"
                ))
            
            if value > maxLoan:
                return await message.send(embed=errorMsg(
                    f"You can only loan up to `{maxLoan} Credits`!"
                ))

            if u.getData('loan')['amount'] > 0:
                return await message.send(embed = errorMsg(
                    f"You already have a loan active that expires <t:{u.getData('loan')['expires']}:R>!\nYou must repay your loan before requesting another loan."
                ))

            loan = {
                "amount": value,
                "interest": round(random.randint(10, 20) / 100, 2),
                "expires": int(time.time() + 60*60*24*7)
            }

            u.addBalance(credits = value)
            u.setValue('loan', loan)

            await message.send(embed = successMsg(
                description = f"Succesfully loaned `{value} Credits` with a {round(loan['interest'] * 100)}% interest.\nMake sure to repay your loan within 1 week!"
            ))