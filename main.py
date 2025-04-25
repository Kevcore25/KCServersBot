"""
PIP REQUIREMENTS:
pip install requests mcstatus discord.py names matplotlib scipy python-dotenv
"""
print("Importing libraries")

import discord, json, random, time, traceback
from discord.ext import commands, tasks
import time, os
from users import User
import users as usersFile
from traceback import print_exc as printError
from dotenv import load_dotenv
from calculatefuncs import *

print("Importing commands...")
import cmds

print("Finished importing")
load_dotenv()



with open("botsettings.json", 'r') as f:
    botsettings = json.load(f)

    KMCExtractLocation = botsettings['KMCExtract']
    prefix = botsettings['prefix']
    inflationAmt = botsettings['inflation amount']
    adminUsers = botsettings['admins']
    botAIChannel = botsettings['AI Channel']
    serverID = botsettings['Server ID']

activity = discord.Activity(type=discord.ActivityType.watching, name=f"KCMC Servers (V.5.5)")
bot = commands.Bot(
    command_prefix=[prefix], 
    case_insensitive=True, 
    activity=activity, 
    status=discord.Status.online,
    intents=discord.Intents().all()
)

if "shopstock.json" not in os.listdir():
    with open("shopstock.json", "x") as f: 
        f.write("{}")

# Remomve help command
bot.remove_command('help')

previousba = 0
botactive = 0

@tasks.loop(seconds = 3)
async def botAI():
    global botactive, previousba

    user = bot.user.id

    u = User(user)
    data = u.getData()

    credits, unity, gems = data['credits'], data['unity'], data['gems']

    def get_user(user: str):
        with open(f"users/{user}.json", "r") as f:
            return json.load(f) 
    
        
    channel = bot.get_channel(botAIChannel)

    # Commands
    async def run(command, **args):
        try:

            try:
                message = await channel.send(f"""[[Main bot]](http://DEBUG/ActiveState:{botactive}/Chance:{round(1 / (106 - botactive * 5) * 100 if botactive > 0 else 0.2, 2)}%) {prefix}{command} {' '.join((f'"{i}"' if ' ' in str(i) else str(i)) for i in args.values())}""")
            except:
                printError()
                message = await channel.send(f"[BOT] {prefix}{command}")

            ctx = await bot.get_context(message)
            return await ctx.invoke(bot.get_command(command), **args)
        except:
            printError()

    # Daily
    if (time.time() - data["dailyTime"] > 60*60*12) and (random.randint(0,99) == 0):
        await run('daily')
    # Hourly
    if time.time() - data["hourlyTime"] > 60*60:
        await run('hourly')

    # Determine the chance based on botactive
    if botactive > 0:
        r = random.randint(0, (105 - botactive * 5))
    else:
        r = random.randint(0, 499)

    if botactive >= 1: botactive -= 1

    previousba = botactive

    match r:
      #  case 0: await rob()
        case 1: 
            for i in range(2): 
                if credits >= 0: await run('beg')
        case 2: 
            if round(credits / 100) > 0: 
                await run('crashgame', betAmount = round(credits/100 if credits < 10000 else 100), autoCash = random.randint(11, 20) / 10)
       # case 3: (await run('beg') for i in range(2))
        case _:
            pass
        
    # When balance is negative, give the bot some starting money
    if credits <= 0: await run('set', key="credits", value = 100)
    

# To create a help description, add help="help description" to bot.command()
# If you do not want the command to be shown in help, add hidden = True
@bot.command(
    help = "Shows information about a bot command.",
    description = \
f"""**How to use the help command**:\nThe help command returns a list of all bot commands as well as a basic description under each command.\nThe help command can be specified with a command as an argument to obtain more details about the command.\n\n**How to read arguments**:\nEach argument that is enclosed with arrows (<>) means the argument is __mandatory__, meaning that you must specify it when running the command.\nAn argument enclosed with square brackets ([]) means that the argument is __optional__, and you do not need to specify it for the command to work properly.\nFor example, the current help command format is: `{prefix}help [command]`\nSince you specified the help command, it returned this message."""
)
async def help(message: discord.Message, commandOrPage: str = "1"): # command is an argument
    """
    Help command

    :params command: Page number or command
    """
    embed = discord.Embed(
        title = "Help",
        color=0xFF00FF
    )
    # Due to the help command only supporting up to 25 commands, this command now splits the commands into pages that contain 10 commands each
    commandsPerPage = 10

    # This means a rewrite of the code is needed

    # If a number on command is not specified then it is probably a detailed view. In that case,
    if not str(commandOrPage).isdigit():
        commandOrPage = commandOrPage.lstrip(prefix)
        if commandOrPage in bot.all_commands:
            cmd = commandOrPage
            originalcmd = str(bot.get_command(commandOrPage))

            description = f"**{prefix}{originalcmd}**\n"

            cmdHelp = bot.all_commands[cmd].help
            if cmdHelp is None: 
                cmdHelp = "No basic description provided"
            
            description += cmdHelp

            if bot.all_commands[cmd].description != "":
                description += "\n\n**Description:**\n" + bot.all_commands[cmd].description
    

            # Aliases
            aliases = bot.all_commands[cmd].aliases
            # Prevent repeating
            if len(aliases) > 0: 
                description += "\n\n**Aliases:**\n" + ", ".join(prefix+i for i in aliases)

            # Format
            description += "\n\n**Detected Command Format:**" + formatParamsMulti(bot.all_commands[cmd]) 

            embed.description = description

            # Reward
            u = User(message.author.id)

            data = u.getData()

            if "helpCmds" not in data:
                u.setValue("helpCmds", [])

            cmdsUsed = u.getData('helpCmds')
            if originalcmd not in cmdsUsed and not bot.get_command(commandOrPage).hidden:
                cmdsUsed.append(originalcmd)
                u.setValue("helpCmds", cmdsUsed)
                u.addBalance(gems=1)
                embed.set_footer(text="+1 Gem due to viewing the details about this command for the first time!")

        else:
            embed.description = f"Command `{commandOrPage}` is not a vaild command!"

        await message.send(embed=embed)
        return
    # Otherwise, it is probably a page number. Therefore...

    def get_help_commands(page: int = 1) -> discord.Embed:
        # Step 1: Obtain all commands and remove aliases and stuff
        cmds: dict[str: str] = {} 

        for cmd in bot.all_commands:
            if bot.get_command(cmd).hidden: 
                continue

            cmdHelp = bot.all_commands[cmd].help
            if cmdHelp is None: 
                cmdHelp = "No description"

            # Aliases
            aliases = bot.all_commands[cmd].aliases
            # Prevent repeating
            if cmd in aliases: continue 

            cmds[cmd] = cmdHelp

        # Sort commands by alphabetical order
        cmds = dict(sorted(cmds.items()))

        # Step 2. Determine page
        # Can be done by doing some math. Start index should be (page - 1)(commandsPerPage) and end should be (startIndex + commandsPerPage -1)

        startI = (page - 1) * commandsPerPage
        endI = (startI + commandsPerPage - 1) # -1 + 1 cancels. (see for loop) but -1 for readability

        # Step 3. Write embeds
        for i in range(startI, endI + 1):
            # If it is out of index, just exit the for loop and send the message
            try:
                cmd = list(cmds)[i]
            except IndexError: 
                break
            desc = cmds[cmd]
            embed.add_field(name = prefix + cmd, value = desc, inline=False)

        embed.set_footer(text=f"Use {prefix}help [command] to display detailed information about a command. \nThe first time you run a detailed help command about a command, you will gain 50 Credits.\nUse {prefix}help [page] to go to another page. Current page: {page}/{len(cmds) // commandsPerPage + 1}")

        return embed

    # Step 4. Send embed to chat
    await message.send(embed=get_help_commands(int(commandOrPage)))

@bot.event
async def on_ready():    
    usersFile.botID = str(bot.user.id)
    print("Bot online!")

    print("Registering commands...")

    # ADD CMDS
    await bot.add_cog(cmds.AccountViewers(bot))
    await bot.add_cog(cmds.AccountUtils(bot))
    await bot.add_cog(cmds.AdminCmds(bot))
    await bot.add_cog(cmds.BalanceGraphs(bot))
    await bot.add_cog(cmds.Exchanges(bot))
    await bot.add_cog(cmds.GambleGames(bot))
    await bot.add_cog(cmds.Informations(bot))
    await bot.add_cog(cmds.LeaderboardCog(bot))
    await bot.add_cog(cmds.TimeIncomes(bot))
    await bot.add_cog(cmds.InteractionGames(bot))
    await bot.add_cog(cmds.CrashGameCog(bot))
    await bot.add_cog(cmds.CardGames(bot))
    await bot.add_cog(cmds.ShopCog(bot))
    await bot.add_cog(cmds.QuestionsQuiz(bot))
    await bot.add_cog(cmds.MCGuessingGames(bot))

    print("Done! Starting bot AI loop...")

    # Start Loops
    await botAI.start()


@bot.event
async def on_message(message: discord.Message):
    global botactive
    await bot.process_commands(message)

    content = message.content

    if content.startswith(prefix):
        botactive += 5
        if botactive > 20:
            botactive = 20

@bot.event 
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
          
        embed=discord.Embed(title="Command on cooldown!",description=f"{ctx.author.mention}, you can use the `{ctx.command}` command <t:{int(time.time() + round(error.retry_after))}:R>", color=0xff0000)
        await ctx.send(embed=embed)
    elif isinstance(error, commands.errors.MemberNotFound): #or if the command isnt found then:
        embed=discord.Embed(description=f"The member you specified is not vaild!", color=0xff0000)
        (ctx.command).reset_cooldown(ctx)
        await ctx.send(embed=embed)
    elif isinstance(error, commands.errors.BadArgument): #or if the command isnt found then:
        params = ctx.command.clean_params
        embed=discord.Embed(description=f"Invalid command arguments!\nCommand format:\n`{prefix}{ctx.command} {formatParamsOneLine(params)}`", color=0xff0000)
        (ctx.command).reset_cooldown(ctx)
        await ctx.send(embed=embed)
    elif isinstance(error, commands.errors.CommandNotFound): #or if the command isnt found then:
        cmd = (ctx.message.content + " ")[len(prefix):].split(" ")[0]
        if cmd.replace("!", "") != "": 
            embed=discord.Embed(description=f"`{cmd}` is not a valid command!", color=0xff0000)
            await ctx.send(embed=embed)
    elif isinstance(error, commands.errors.ConversionError): #or if the command isnt found then:
        embed=discord.Embed(description=f"A conversion error occurred! Check to see if you have the correct format for arguments.", color=0xff0000)
        (ctx.command).reset_cooldown(ctx)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title='A FATAL error occurred:', colour=0xEE0000) #Red
        embed.add_field(name='Reason:', value=str(error).replace("Command raised an exception: ", '')) 
        if "KeyError" in str(error):
            if str(error).replace("Command raised an exception: ", '').replace("KeyError: ", "").replace("'", "") in usersFile.userTemplate:
                embed.description = "*This is most likely due to account errors.*"
        print(traceback.format_exc())
        await ctx.send(embed=embed)
        (ctx.command).reset_cooldown(ctx)

# Run the bot based on the token in the .env file
bot.run(os.getenv("DISCORD_TOKEN"))
