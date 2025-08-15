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
botchannel = input("Bot Channel ID: ")

print("3. What is the file location for the KMCExtract folder?\nThis should be the folder and not the location of the users.json file.\nIf you don't have KMCExtract or are not planning to use the KCash exchange service, just leave it blank.")
kmceLocation = input("KMCExtract Folder Location: ")

settings = {
    "admins": [], # More advanced optoin which is optional
    "prefix": prefix, # Prefix of the bot for it to work
    "inflation amount": 500, # At what avg. credits will inflation start increasing
    "KMCExtract": kmceLocation, # KMCExtract location which only affects KCash exchange service
    "AI Channel": botchannel, # Bot AI channel which the bot sends messages to. Note that the bot needs permission in this channel!
    "Server ID": 0, # This seems to not be in use, so it won't be asked in the script
    "KCash Rate": 0.01,
    "Exchange fee": [500, 5],
    "Debug": False
}

with open('botsettings.json', 'w') as f:
    json.dump(settings, f, indent=4)

print("Done! Your bot should operate now!\nYou can edit more advanced settings in the botsettings.json file!")