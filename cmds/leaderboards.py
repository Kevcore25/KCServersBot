import discord
from discord.ext import commands
from calculatefuncs import *

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        

    @commands.command(
        help = "Display the people with the most Credits",
        aliases = ["lb"]
    )
    async def leaderboard(self, message):
        embed = discord.Embed(
            title = "Top members with the most Credits",
            color = 0xFF00FF
        )

        usersDir = os.listdir('users')

        users = {}
        for file in usersDir:
            if file == "main.json": continue
            with open('users/' + file, 'r') as f:
                try:
                    data = json.load(f)
                    c = float(data['credits'])
                    if c != 0 and data.get('settings', {}).get("publicity", True): users[file.replace(".json", '')] = c
                except: pass

        totalCredits = 0

        sortedUsers = sorted(users.items(), key=lambda x:x[1], reverse=True)

        for i in range(len(sortedUsers)):
            try:
                usr = sortedUsers[i]

                user = self.bot.get_user(int(usr[0]))

                totalCredits += usr[1]
                try:
                    embed.add_field(name=f"{i + 1}. {user.display_name}", value=f"Credits: ≈{get_prefix(usr[1])}")
                except AttributeError:
                    embed.add_field(name=f"{i + 1}. Unknown", value=f"Credits: ≈{get_prefix(usr[1])}")
            except Exception as e:
                embed.add_field(name=f"{i + 1}. Error", value=f"Reason: {e}")

        # Inflation % = Total Credits of Members / (Inflation amount * Amount of Members) x 100 (%)
        inflationLvl = totalCredits / (inflationAmt * (i+1)) * 100
        if inflationLvl < 100: inflationLvl = 100

        # Average credits = total / number of users
        avgcredits = totalCredits / (i+1)

        embed.description = f"**Total Credits**: `{numStr(totalCredits)}`\n**Inflation**: `{round(calcInflation() * 100)}%`\n**Average Credits**: `{numStr(avgcredits)}`"

        await message.send(embed=embed)

    @commands.command(
        help = "Display the people with the most Credits",
        aliases = ["lbs", 'slb', 'leaderboardscore']
    )
    async def scoreleaderboard(self, message):
        embed = discord.Embed(
            title = "Top members with the most score",
            color = 0xFF00FF
        )

        usersDir = os.listdir('balanceLogs')

        users = {}
        for file in usersDir:
            if file == "main": continue

            if botsettings.get('settings', {}).get("publicity", True): 
                users[file.replace(".json", '')] = calcScore(User(file.replace(".json", '')))

        totalCredits = 0

        sortedUsers = sorted(users.items(), key=lambda x:x[1], reverse=True)

        for i in range(len(sortedUsers)):
            try:
                usr = sortedUsers[i]

                user = self.bot.get_user(int(usr[0]))

                totalCredits += usr[1]
                try:
                    embed.add_field(name=f"{i + 1}. {user.display_name}", value=f"Score: ≈{get_prefix(usr[1])}")
                except AttributeError:
                    embed.add_field(name=f"{i + 1}. Unknown", value=f"Score: ≈{get_prefix(usr[1])}")
            except Exception as e:
                embed.add_field(name=f"{i + 1}. Error", value=f"Reason: {e}")

        # Average credits = total / number of users
        avgcredits = totalCredits / (i+1)

        embed.description = f"**Average Score**: `{numStr(avgcredits)}`"

        await message.send(embed=embed)


    @commands.command(
        help = "Display the people with the most Wealth (Credits + Stock + Unity)",
        aliases = ["lbw", 'wlb', 'leaderboardwealth']
    )
    async def wealthleaderboard(self, message):
        embed = discord.Embed(
            title = "Top members with the most wealth",
            color = 0xFF00FF
        )

        usersDir = os.listdir('balanceLogs')

        users = {}
        for file in usersDir:
            if file == "main": continue

            if botsettings.get('settings', {}).get("publicity", True): 
                users[file.replace(".json", '')] = calcWealth(User(file.replace(".json", '')))

        totalCredits = 0

        sortedUsers = sorted(users.items(), key=lambda x:x[1], reverse=True)

        for i in range(len(sortedUsers)):
            try:
                usr = sortedUsers[i]

                user = self.bot.get_user(int(usr[0]))

                totalCredits += usr[1]
                try:
                    embed.add_field(name=f"{i + 1}. {user.display_name}", value=f"Wealth: ≈{get_prefix(usr[1])}")
                except AttributeError:
                    embed.add_field(name=f"{i + 1}. Unknown", value=f"Wealth: ≈{get_prefix(usr[1])}")
            except Exception as e:
                embed.add_field(name=f"{i + 1}. Error", value=f"Reason: {e}")

        # Average credits = total / number of users
        avgcredits = totalCredits / (i+1)

        embed.description = f"**Average Wealth**: `{numStr(avgcredits)}`"

        await message.send(embed=embed)

