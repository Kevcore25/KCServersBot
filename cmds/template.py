import discord
from discord.ext import commands
from calculatefuncs import *

DESC = ''''''

class TemplateCog(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        
    @commands.command(
        help = f"Template Command",
        description = DESC,
        aliases = ['templatecmd'],
    )
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def template(self, message: Context):
        user = User(message.author.id)

