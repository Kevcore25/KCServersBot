import discord
from discord.ext import commands
from calculatefuncs import *
import asyncio
class AdminUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        


    @commands.command(aliases=['del', 'purge', 'clear', 'clr', 'admin.delete', 'admin.purge', 'admin.clear', 'removeMessages', ])
    @commands.has_permissions(manage_channels=True) # Requires permission to manage channels
    async def delete(self, message: discord.ext.commands.Context, delamount=-1):        
        if delamount > 0:
            embed=discord.Embed(title=f"Deleting messages...", description=f"Trying to delete {delamount} messages...", color=0x00CCFF)
            await message.send(embed=embed, delete_after=120)
            await message.channel.purge(limit=delamount+2)

            embed=discord.Embed(title=f"Success", description=f"Deleted {delamount} messages in this channel", color=0x00CCFF)
            await message.send(embed=embed, delete_after=5)
        else:
            embed=discord.Embed(title=f"Command requires integer argument higher than 0!", color=0xFF0000)

            await message.send(embed=embed, delete_after=120)        


    @commands.command()
    @commands.has_permissions(manage_channels=True) # Requires permission to manage channels
    async def slowmode(self, ctx: discord.ext.commands.Context, seconds: int):
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                await ctx.send(f"Slowmode has been **disabled** in {ctx.channel.mention}!", delete_after=5)
            else:
                await ctx.send(f"I've set the slowmode to **{seconds}** seconds in {ctx.channel.mention}!", delete_after=5)
        except discord.Forbidden:
            await ctx.send("I do not have the necessary permissions to manage channels.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")