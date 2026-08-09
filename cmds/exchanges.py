import discord
from discord.ext import commands
from calculatefuncs import *
import math

class Exchanges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        help = f"Converts gems into another currency. Run the command by itself for more info.",
        description = f"""Conversion rates can be found by running the command by itself.\nFormat of command: `{prefix}gemexchange [currency <amount>]`\n\n-# Exchange Terms:\n-# I will keep this concise: You must use this exchange service as intended. No exploitations of this service, whether it were to be an issue with the system, or an intentional exploit, is prohibited. Also don't forget that your KCMC account (KCash account) can be changed at any time without prior notice.""",
        aliases = ["ge", "gemconvert"]
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def gemexchange(self, message, currency = None, amount = 0):
        user = User(message.author.id)
        data = user.getData()
        
        exchangeRates = {
            ("gems", "unity"): 1,
            ("gems", "credits"): round(5 * calcInflation()),
            ("gems", "kcash"): 1000,
        }

        if currency is None:
            exchangeRateTxt = "\n".join(f"1 gem > {exchangeRates[(f,t)]} {t}" for f, t in exchangeRates)
            embed = discord.Embed(title="Exchange information", description=f"""Format: `{prefix}gemexchange [to currency] <amount of gems to exchange>`\n\n**Exchange rates**:\n{exchangeRateTxt}""", color=0xFF00FF)

        elif currency.lower() not in ['credits','unity', 'kcash']:
            embed = discord.Embed(title="Not a valid exchange currency!",description=f"Your exchange from currency is not valid! Valid options are credits, unity, and kcash", color=0xFF0000)
        elif not str(amount).isnumeric() or int(amount) <= 0:
            embed = discord.Embed(title="Amount invaild!",description=f"Your amount must be an integer greater than 0!", color=0xFF0000)
        else:
            currency = currency.lower()
            for f, t in exchangeRates:
                if f == "gems" and t == currency:
                    exchangeRate = exchangeRates[(f,t)]
                    if data[f] < amount:
                        embed = discord.Embed(title="Not enough currency!",description=f"Your {f.capitalize()} amount is less than the requested exchange amount which requires {amount}!", color=0xFF0000)
                    elif data['loan']['amount'] > 0:
                        embed = errorMsg("You cannot use the KCash exchange service while you have a loan active!\nPlease repay your loan in order to exchange your Credits into KCash.")
                    else:
                        getAmount = round(amount * exchangeRate, 5)

                        if t == "credits":
                            user.addBalance(credits = getAmount, gems = -amount)

                        elif t == "kcash":
                            ign = user.getData('settings').get("ign", None)
                            r = kmce_server_request(f"ADD {getAmount} FOR {ign}")

                            if r.get("success", False):
                                user.addBalance(gems = -amount)
                                embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} Gems` into `{getAmount} KCash`", color=0x00FF00)
                                
                            else:
                                embed = discord.Embed(title="Exchange failed!",description=f"There was an error processing your KCash account.\nYou are not charged for this exchange.\n-# Reason: {r.get("reason", "Malformed return output")}", color=0xFF0000)
                            break

                        else:
                            user.addBalance(unity = getAmount, gems = -amount)

                        embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} Gems` into `{getAmount} {t.capitalize()}`", color=0x00FF00)
                    break

            else:
                embed = discord.Embed(title="Not a valid exchange currency!",description=f"Your exchange currencies is not valid! Run `{prefix}exchange` to see the details.", color=0xFF0000)


        await message.send(embed=embed)

    @commands.command(
        help = f"Converts Credits into KCash",
        description = f"""Conversion rates can be found by running the command by itself.\n\n-# Exchange Terms:\n-# I will keep this concise: You must use this exchange service as intended. No exploitations of this service, whether it were to be an issue with the system, or an intentional exploit, is prohibited. Also don't forget that your KCMC account (KCash account) can be changed at any time without prior notice.""",
        aliases = ["convert", "change"],
        hidden = True
    )
    @commands.cooldown(1, 30, commands.BucketType.user) 
    async def exchange(self, message, amount: float = None):
        user = User(message.author.id)
        data = user.getData()
        inflation = calcInflation()

        with open("botsettings.json", 'r') as f:
            botsettings: dict = json.load(f)
        
        kcashrate = round(botsettings.get('KCash rate', 0.1) / inflation, 5)
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
            embed = discord.Embed(title="Exchange information", description=f"""Format: `{prefix}exchange <credits>`\n\nCurrently, it would be `1 Credit` → `{kcashrate} KCash`\n\n**Exchange fee**: `{exchangeFee[0]} Credits` and `{exchangeFee[1]} Unity` per exchange.""", color=0xFF00FF)
            embed.set_footer(text="Credit exchange fee can be lowered with higher Wealth Power.\nWealth Power perks (e.g. Pacifist) are not taken into account.")

            self.exchange.reset_cooldown(message)


        elif amount <= 0:
            embed = discord.Embed(title="Amount invaild!",description=f"Your amount must be an integer greater than 0!", color=0xFF0000)
            self.exchange.reset_cooldown(message)
        else:
            # Check if user is vaild to exchange
            
            # If amount is more than balance
            if (amount + exchangeFee[0]) > data['credits']:
                embed = discord.Embed(
                    title="Not enough Credits!",
                    description=f"Your balance is less than the requested exchange amount which requires `{amount + exchangeFee[0]} Credits`!", 
                    color=0xFF0000
                )
                self.exchange.reset_cooldown(message)
            # Check unity
            elif data['unity'] < exchangeFee[1]:
                embed = discord.Embed(
                    title="Not enough Unity!",
                    description=f"Your Unity balance is less than the exchange fee of `{exchangeFee[1]} Unity`!", 
                    color=0xFF0000
                )
                self.exchange.reset_cooldown(message)
            else:
                ign = user.getData('settings').get("ign", None)

                getAmount = round(amount * kcashrate)

                # Round Value
                r = kmce_server_request(f"ADD {getAmount} FOR {ign}")

                if r.get("success", False):
                    user.addBalance(credits = -amount)
                    embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} Credits` to `{getAmount} KCash`.\nExchange fee: `{exchangeFee[0]} Credits`, `{exchangeFee[1]} Unity`", color=0x00FF00)
                    # Exchange fee
                    user.addBalance(credits = -exchangeFee[0], unity = -exchangeFee[1])

                    # Add for score calcs
                    user.addValue("kcashExchanged", amount)

                else:
                    embed = discord.Embed(title="Exchange failed!",description=f"There was an error processing your KCash account.\nYou are not charged for this exchange.\n-# Reason: {r.get("reason", "Malformed return output")}", color=0xFF0000)
    
        await message.send(embed=embed)


    @commands.command(
        help = f"Converts KCash into Credits",
        description = f"""Conversion rates can be found by running the command by itself.\n\n-# Exchange Terms:\n-# I will keep this concise: You must use this exchange service as intended. No exploitations of this service, whether it were to be an issue with the system, or an intentional exploit, is prohibited. Also don't forget that your KCMC account (KCash account) can be changed at any time without prior notice.""",
        aliases = ["extractkcash", "loadkcash"],
        hidden = True
    )
    @commands.cooldown(1, 30, commands.BucketType.user) 
    async def extract(self, message, amount: int = None):
        user = User(message.author.id)
        data = user.getData()
        inflation = calcInflation()

        with open("botsettings.json", 'r') as f:
            botsettings: dict = json.load(f)
        
        kcashrate = round(inflation / botsettings.get('KCash rate', 1), 5)
        exchangeFee = 100
        ign = user.getData('settings').get("ign", None)

        # Lower exchange rate based on Wealth Power
        try:
            exchangeFee = round(
                (exchangeFee * 2) 
                /
                math.log10(calcWealthPower(user, noperks=True)),
            2)
        except ValueError: # Logarithm of 0
            exchangeFee = 100
            
        # exchange fee cannot be higher than initial
        exchangeFee = round(min(100, exchangeFee))


        if amount is None:
            embed = discord.Embed(title="Exchange information", description=f"""Format: `{prefix}extract <credits>`\n\nCurrently, it would be `1 KCash` → `{kcashrate} Credits`\n\n**Exchange fee**: `{exchangeFee} KCash` per exchange.""", color=0xFF00FF)
            embed.set_footer(text="KCash exchange fee can be lowered with higher Wealth Power.\nWealth Power perks (e.g. Pacifist) are not taken into account.")
            self.extract.reset_cooldown(message)
        elif amount <= 0:
            embed = discord.Embed(title="Amount invaild!",description=f"Your amount must be an integer greater than 0!", color=0xFF0000)
            self.extract.reset_cooldown(message)
        elif ign is None:
            embed = errorMsg(title = "No IGN set", description=f"You need to set up a Minecraft username and __verify it*__ in order to use this extract service.\n\n-# Verify Qualification: You need to join an official KCMC server with a version 1.3+ KMCEv3 plugin, and then run `.kcslink {user.ID}`")
            self.extract.reset_cooldown(message)
        else:
            # Check if user is vaild to exchange
            r = kmce_server_request(f"READ discordid FOR {ign}")
            bal = kmce_server_request(f"READ bal FOR {ign}").get('output', 0)
            amount = int(amount)

            if r.get('output') != str(user.ID):
                embed = errorMsg(title = "IGN and Discord ID does not match!", description=f"You need to verify your Discord account in-game by running `.kcslink {user.ID}`!\n\n-# Expected: {user.ID} but got: {r.get('output')}")
                self.extract.reset_cooldown(message)

            # If amount is more than balance
            elif (amount + exchangeFee) > bal:
                embed = discord.Embed(
                    title="Not enough KCash!",
                    description=f"Your balance is less than the requested exchange amount which requires `{amount + exchangeFee} KCash`!\n-# You only have {bal} KCash.", 
                    color=0xFF0000
                )
                self.extract.reset_cooldown(message)
            else:
                getAmount = round(amount * kcashrate, 5)

                # Round Value
                r = kmce_server_request(f"ADD -{amount+exchangeFee} FOR {ign}")

                if r.get("success", False):
                    user.addBalance(credits = getAmount)
                    embed = discord.Embed(title="Exchange successful!",description=f"Exchanged `{amount} KCash` to `{getAmount} Credits`.\nExchange fee: `{exchangeFee} KCash`", color=0x00FF00)

                else:
                    embed = discord.Embed(title="Exchange failed!",description=f"There was an error processing your KCash account.\n-# Reason: {r.get("reason", "Malformed return output")}", color=0xFF0000)


     


        await message.send(embed=embed)
