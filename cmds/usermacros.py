from discord.ext import commands
from calculatefuncs import *
import requests
from copy import copy
macroMsg = lambda n: f"""
This is a user macro command. If an argument is specified, the macro is overwritten and set. You can use this command to define custom macros. 
Separate different commands using a semicolon (;) or a new line. 
For example, to set a macro that runs hourly and work, you can do:
```
{P}macro{n} {P}hourly;{P}work work
``` or ```
{P}macro{n}
{P}hourly
{P}work work
```*(all within the same message)*

Each macro has a limit on the character length and the number of commands. You may not exceed 100 characters or 5 commands within a single macro.

You may run macros within a macro; however, keep in mind that each macro has a cooldown and can only be ran twice within that cooldown.
You are not allowed to abuse the macro system intentionally to cause lag. You will lose access to this feature if this is found.
"""

class UserMacros(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    async def runmacro(self, ctx: Context, text: str | None, number: int):
        """Runs, or assigns a macro"""

        user = User(ctx.author.id)

        if user.has_tag("macroban"):
            return
        
        # Runs a macro
        if text is None:
            # Get macro
            cmds: str = user.getData(f"m{number}")

            if cmds is None:
                return await ctx.send(embed = errorMsg(f"You do not have macro #{number} set up!"))

            # Try to create and run the commands
            for cmd in cmds:
                msg = copy(ctx.message)
                msg.content = cmd

                new_ctx = await self.bot.get_context(msg)

                if new_ctx.command is None:
                    continue

                await self.bot.invoke(new_ctx)

            await ctx.send(embed=successMsg(description="All macros have ran successfully!"))
        else:
            # Cannot exceed 100 char
            if len(text) > 100:
                return await ctx.send(embed = errorMsg("You may not exceed over 100 characters for your macro!"))

            cmds = text.replace('\n', ';').split(';')

            # Cannot exceed 5 cmds            
            if len(cmds) > 5:
                return await ctx.send(embed = errorMsg("You may not exceed over 5 commands in one macro!"))

            # Check to see if the commands exist
            for cmd in cmds.copy():
                msg = copy(ctx.message)
                msg.content = cmd
                if (await self.bot.get_context(msg)).command is None:
                    await ctx.send(embed = discord.Embed(
                        color = 0xFFAA00,
                        description= f"The command `{cmd}` is not found!",
                        title= "Warning"
                    ))
                    cmds.remove(cmd)

            if len(cmds) == 0: 
                user.setValue(f"m{number}", None)
                return await ctx.send(embed=errorMsg(f"There are no valid commands in your macro!\nMacro #{number} has been disabled."))

            user.setValue(f"m{number}", cmds)

            await ctx.send(embed=successMsg(title = "Your macro has been set!", description = "These commands will be ran in the following order: " + "".join(f"\n- `{cmd}`" for cmd in cmds)))
    
    @commands.command(
        help = "User-defined Macro #1",
        description=macroMsg(1),
        aliases = ["m1", "1"]
    )
    @commands.cooldown(2, 10, commands.BucketType.user) 
    async def macro1(self, ctx, *, text: str = None):
        await self.runmacro(ctx, text, 1)

    @commands.command(
        help = "User-defined Macro #2",
        description=macroMsg(2),
        aliases = ["m2", "2"]
    )
    @commands.cooldown(2, 10, commands.BucketType.user) 
    async def macro2(self, ctx, *, text: str = None):
        await self.runmacro(ctx, text, 2)

    @commands.command(
        help = "User-defined Macro #3",
        description=macroMsg(3),
        aliases = ["m3", "3"]
    )
    @commands.cooldown(2, 10, commands.BucketType.user) 
    async def macro3(self, ctx, *, text: str = None):
        await self.runmacro(ctx, text, 3)