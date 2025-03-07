import discord
from discord.ext import commands
from calculatefuncs import *

class TemplateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    