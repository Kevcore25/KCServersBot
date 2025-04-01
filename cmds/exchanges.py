import discord
from discord.ext import commands
from calculatefuncs import *
import math

class Exchanges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        help = f"Converts gems into another currency. Run the command by itself for more info.",
        description = f"""Conversion rates can be found by running the command by itself.\nFormat of command: `{prefix} [currency <amount>]`""",
        aliases = ["ge", "gemconvert"]
    )
    async def gemexchange(self, message, currency = None, amount = 0):
        user = User(message.author.id)
        data = user.getData()
        
        exchangeRates = {
            ("gems", "unity"): 1,
            ("gems", "credits"): round(5 * calcInflation()),
        }

        if currency is None:
            exchangeRateTxt = "\n".join(f"1 {f} > {exchangeRates[(f,t)]} {t}" for f, t in exchangeRates)
            embed = discord.Embed(title="Exchange information", description=f"""Format: `{prefix}gemexchange [to currency] <amount of gems to exchange>`\n\n**Exchange rates**:\n{exchangeRateTxt}""", color=0xFF00FF)

        elif currency not in ['credits','unity']:
            embed = discord.Embed(title="Not a valid exchange currency!",description=f"Your exchange from currency is not valid! Valid options are credits and unity.", color=0xFF0000)
        elif not str(amount).isnumeric() or int(amount) <= 0:
            embed = discord.Embed(title="Amount invaild!",description=f"Your amount must be an integer greater than 0!", color=0xFF0000)
        else:
        
            for f, t in exchangeRates:
                if f == "gems" and t == currency:
                    exchangeRate = exchangeRates[(f,t)]
                    if data[f] < amount:
                        embed = discord.Embed(title="Not enough currency!",description=f"Your {f.capitalize()} amount is less than the requested exchange amount which requires {amount}!", color=0xFF0000)
                    else:
                        getAmount = round(amount * exchangeRate, 5)

                        if t == "credits":
                            user.addBalance(credits = getAmount, gems = -amount)
                        else:
                            user.addBalance(unity = getAmount, gems = -amount)

                        embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} Gems` into `{getAmount} {t.capitalize()}`", color=0x00FF00)
                    break

            else:
                embed = discord.Embed(title="Not a valid exchange currency!",description=f"Your exchange currencies is not valid! Run `{prefix}exchange` to see the details.", color=0xFF0000)


        await message.send(embed=embed)

    @commands.command(
        help = f"Converts Credits into KCash",
        description = f"""Conversion rates can be found by running the command by itself.\n""",
        aliases = ["convert", "change"],
        hidden = True
    )
    async def exchange(self, message, amount: float = None):
        user = User(message.author.id)
        data = user.getData()
        inflation = calcInflation()

        with open("botsettings.json", 'r') as f:
            botsettings: dict = json.load(f)
        
        kcashrate = botsettings.get('KCash rate', 0.1)
        exchangeFee = botsettings.get('Exchange fee', [500, 5])

        # Lower exchange rate based on Wealth Power
        try:
            exchangeFee[0] = round(
                (exchangeFee[0] * 2) 
                /
                math.log10(calcWealthPower(user, noperks=True)),
            2)
        except ValueError: # Logarithm of 0
            exchangeFee[0] = 500
            
        # exchange fee cannot be higher than initial
        if exchangeFee[0] > 500: exchangeFee[0] = 500


        if amount is None:
            embed = discord.Embed(title="Exchange information", description=f"""Format: `{prefix}exchange <credits>`\n\nCurrently, it would be `1 Credit` → `{round(kcashrate / inflation, 4)} KCash`\n\n**Exchange fee**: `{exchangeFee[0]} Credits` and `{exchangeFee[1]} Unity` per exchange.""", color=0xFF00FF)
            embed.set_footer(text="Credit exchange fee can be lowered with higher Wealth Power.\nWealth Power perks (e.g. Pacifist) are not taken into account.")

        elif amount <= 0:
            embed = discord.Embed(title="Amount invaild!",description=f"Your amount must be an integer greater than 0!", color=0xFF0000)
        else:
            # Check if user is vaild to exchange
            
            # If amount is more than balance
            if (amount + exchangeFee[0]) > data['credits']:
                embed = discord.Embed(
                    title="Not enough Credits!",
                    description=f"Your balance is less than the requested exchange amount which requires `{amount + exchangeFee[0]} Credits`!", 
                    color=0xFF0000
                )
            # Check unity
            elif data['unity'] < exchangeFee[1]:
                embed = discord.Embed(
                    title="Not enough Unity!",
                    description=f"Your Unity balance is less than the exchange fee of `{exchangeFee[1]} Unity`!", 
                    color=0xFF0000
                )

            else:
                try:
                    with open(os.path.join(KMCExtractLocation, "users.json"), 'r') as file:
                        kmceusers = json.load(file)

                    ign = user.getData('settings').get("IGN", None)

                    getAmount = round(amount * kcashrate, 2)
                    kmceusers[ign]['KCash'] += getAmount

                    with open(os.path.join(KMCExtractLocation, "users.json"), 'w') as file:
                        kmceusers = json.dump(kmceusers, file)       

                    user.addBalance(credits = -amount)

                    # Exchange fee
                    user.addBalance(credits = -exchangeFee[0], unity = -exchangeFee[1])


                    embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} Credits` to `{getAmount} KCash`.\nExchange fee: `{exchangeFee[0]} Credits`, `{exchangeFee[1]} Unity`", color=0x00FF00)

                except KeyError:
                    embed = discord.Embed(title="Not registered!",description=f"Your MC Username (`{ign}`) is not registered on KMCExtract!", color=0xFF0000)

        await message.send(embed=embed)
