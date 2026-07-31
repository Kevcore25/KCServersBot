# Script for setup
import json

print("== KCServers Bot Setup Script ==")

# Get Bot Token
print("First, the program needs to get your Discord bot token.\nIf you do not have a bot token, head to the Discord Developer Portal and create a new bot, where you are able to reset the token and view it. Copy it and paste it here")
token = input("Discord Bot Token: ")
with open('.env', 'w') as f:
    f.write("DISCORD_TOKEN=" + token)

# Create Bot settings config
print("Now, the program will create a botsettings.json template. Only necessary values will be asked; you can change more options by editing the file later.")

print("1. What should be prefix of the bot be? (e.g. ! if you want !help)")
prefix = input("Prefix: ")

print("2. What is the channel ID for the bot channel?\nThe channel ID can be obtained by enabling Developer mode in discord and right clicking a channel and selecting Copy ID.\nThis is used for things such as the lottery annoucements and other such bot annoucements.")
botchannel = int(input("Bot Channel ID: "))

settings = {
    "admins": [], # More advanced option which is optional
    "prefix": prefix, # Prefix of the bot for it to work. In V.7.5, you can use an array instead
    "inflation amount": 5000, # At what avg. credits will inflation start increasing
    "KMCExtract": None, # Legacy KMCExtract folder location - no longer used due to KMCEv3 server-sided accounts
    "AI Channel": botchannel, # Bot AI channel which the bot sends messages to. Note that the bot needs permission in this channel!
    "Server ID": 0, # This seems to not be in use, so it won't be asked in the script
    "KCash rate": 1, # Rate of 1 Credit > X KCash. By default (without inflation) due to only integer values, it is 1
    "Exchange fee": [100, 5],
    "Backups": False, # Enable backups to google drive - must be set up beforehand or it won't work
    "Debug": False
}

with open('botsettings.json', 'w') as f:
    json.dump(settings, f, indent=4)

print("Done! Your bot should operate now!\nYou can edit more advanced settings in the botsettings.json file!")