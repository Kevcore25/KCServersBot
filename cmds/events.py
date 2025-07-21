from discord.ext import commands
from calculatefuncs import *
import asyncio
import random
import discord
import time

EVENT_INFO = f"""
Events happen periodically either by time, or by commands.

In an event, **ALL** members have the opportunity to join in.
Although I won't show you a list of all the events, here are some categories you can expect:
* Time-based quizzes (e.g. math)
* Run a specific command

Rewards you can expect:
* Credits
* Unity
* Items
* Gems

"""

class EventsCog(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.active_events = {}  # Track active events by channel_id


    async def tier1Reward(self, context):
        """
        Gives a Tier 1 reward to the user.
        A Tier 1 reward is 2 of the following:
        * +15 Credits
        * +5 Unity
        * +1 Gem
        * +3 Popularity
        """

        user = User(context.author.id)

        rewards = []

        for i in range(2):
            r = random.randint(0, 3)

            match r:
                case 0:
                    user.addBalance(credits=15)
                    rewards.append("15 Credits")
                case 1:
                    user.addBalance(unity=5)
                    rewards.append("5 Unity")
                case 2:
                    user.add_item("Popularity", 3)
                    rewards.append("3 Popularity")
                case 3:
                    user.addBalance(gems=1) 
                    rewards.append("1 Gem")

        embed = discord.Embed(title="Event Reward", description=f"You received the following rewards:\n{', '.join(f'`+{i}`' for i in rewards)}", color=0x00FF00)
        await context.channel.send(embed=embed)
    async def tier2Reward(self, context):
        """
        Gives a Tier 2 reward to the user.
        A Tier 2 reward is 3 of the following:
        * +50 Credits
        * +10 Unity
        * 1 Mini Credit Booster (1h)
        * +2 Gems
        * +12 Popularity
        * +12 Account Viewers
        """

        user = User(context.author.id)

        rewards = []

        for i in range(3):
            r = random.randint(0, 5)

            match r:
                case 0:
                    user.addBalance(credits=50)
                    rewards.append("50 Credits")
                case 1:
                    user.addBalance(unity=10)
                    rewards.append("10 Unity")
                case 2:
                    user.add_item("Mini Credit Booster", 3600, 1)
                    rewards.append("1 Mini Credit Booster (1h)")
                case 3:
                    user.addBalance(gems=3)
                    rewards.append("3 Gems")
                case 4:
                    user.add_item("Popularity", 12)
                    rewards.append("12 Popularity")
                case 5:
                    user.add_item('Account Viewer', -1, 12)
                    rewards.append("12 Account Viewers")

        embed = discord.Embed(title="Event Reward", description=f"You received the following rewards:\n{', '.join(f'`+{i}`' for i in rewards)}", color=0x00FF00)
        await context.channel.send(embed=embed)

    async def tier3Reward(self, context):
        """
        Gives a Tier 3 reward to the user.
        A Tier 3 reward is 3 of the following:
        * +100 Credits
        * +25 Unity
        * 1 Credit Booster (1h)
        * +5 Gems
        """

        user = User(context.author.id)

        rewards = []

        for i in range(3):
            r = random.randint(0, 3)

            match r:
                case 0:
                    user.addBalance(credits=100)
                    rewards.append("100 Credits")
                case 1:
                    user.addBalance(unity=25)
                    rewards.append("25 Unity")
                case 2:
                    user.add_item("Credit Booster", 3600, 1)
                    rewards.append("1 Credit Booster (1h)")
                case 3:
                    user.addBalance(gems=5)
                    rewards.append("5 Gems")

        embed = discord.Embed(title="Event Reward", description=f"You received the following rewards:\n{', '.join(f'`+{i}`' for i in rewards)}", color=0x00FF00)
        await context.channel.send(embed=embed)


    async def tier1Event(self, context):
        """
        Runs a Tier 1 event.
        A Tier 1 event is a simple quiz or command that users can run.
        The reward is a Tier 1 reward.
        """
        
        if context.channel.id in self.active_events:
            return  # Event already running in this channel
        
        event_type = random.randint(0, 4)
        
        match event_type:
            # Simple math question
            case 0:
                a, b = random.randint(1, 50), random.randint(1, 50)
                answer = str(a + b)
                question = f"What is {a} + {b}?"
                
            # Simple multiplication
            case 1:
                a, b = random.randint(1, 12), random.randint(1, 12)
                answer = str(a * b)
                question = f"What is {a} × {b}?"
                
            # Number guessing
            case 2:
                answer = str(random.randint(1, 20))
                question = "Guess a number between 1 and 20!"
                
            # Word scramble
            case 3:
                words = ["python", "discord", "server", "gaming", "credits", "unity"]
                word = random.choice(words)
                scrambled = ''.join(random.sample(word, len(word)))
                answer = word
                question = f"Unscramble this word: **{scrambled}**"
                
            # Color challenge
            case 4:
                colors = ["red", "blue", "green", "yellow", "purple", "orange", "pink"]
                answer = random.choice(colors)
                question = f"Name a color that starts with '{answer[0].upper()}'!"
        
        # Create event embed
        embed = discord.Embed(
            title="🎉 Tier 1 Event Started!",
            description=f"**{question}**\n\nFirst person to answer correctly wins!\n⏰ You have **30 seconds**!",
            color=0x00FF00
        )
        
        event_msg = await context.send(embed=embed)
        
        # Track the event
        self.active_events[context.channel.id] = {
            'answer': answer.lower(),
            'start_time': time.time(),
            'tier': 1,
            'question': question
        }
        
        # Wait for 30 seconds
        await asyncio.sleep(30)
        
        # Check if event is still active (no winner)
        if context.channel.id in self.active_events:
            del self.active_events[context.channel.id]
            timeout_embed = discord.Embed(
                title="⏰ Event Timeout",
                description=f"Nobody answered correctly in time!\nThe answer was: **{answer}**",
                color=0xFF0000
            )
            await context.send(embed=timeout_embed)

    async def tier2Event(self, context):
        """
        Runs a Tier 2 event.
        A Tier 2 event is a more challenging quiz or puzzle.
        The reward is a Tier 2 reward.
        """
        
        if context.channel.id in self.active_events:
            return  # Event already running in this channel
        
        event_type = random.randint(0, 4)
        
        match event_type:
            # Complex math
            case 0:
                a, b, c = random.randint(2, 15), random.randint(2, 15), random.randint(1, 10)
                answer = str(a * b + c)
                question = f"What is {a} × {b} + {c}?"
                
            # Riddle
            case 1:
                riddles = [
                    ("I have keys but no locks. I have space but no room. What am I?", "keyboard"),
                    ("I'm tall when I'm young, and I'm short when I'm old. What am I?", "candle"),
                    ("What has hands but cannot clap?", "clock"),
                    ("What gets wetter the more it dries?", "towel"),
                    ("I have cities but no houses. I have mountains but no trees. What am I?", "map")
                ]
                riddle_data = random.choice(riddles)
                question = riddle_data[0]
                answer = riddle_data[1]
                
            # Sequence puzzle
            case 2:
                start = random.randint(1, 10)
                step = random.randint(2, 5)
                sequence = [start + step * i for i in range(4)]
                next_num = start + step * 4
                answer = str(next_num)
                question = f"What's the next number in the sequence: {', '.join(map(str, sequence))}, ?"
                
            # Word association
            case 3:
                associations = [
                    ("Ice is to cold as fire is to...", "hot"),
                    ("Book is to read as song is to...", "listen"),
                    ("Day is to sun as night is to...", "moon"),
                    ("Fish is to water as bird is to...", "air"),
                    ("Happy is to sad as up is to...", "down")
                ]
                assoc_data = random.choice(associations)
                question = assoc_data[0]
                answer = assoc_data[1]
                
            # Calculation puzzle
            case 4:
                x = random.randint(5, 25)
                y = random.randint(2, 8)
                answer = str(x * 2 + y)
                question = f"If X = {x} and Y = {y}, what is 2X + Y?"
        
        # Create event embed
        embed = discord.Embed(
            title="🎉 Tier 2 Event Started!",
            description=f"**{question}**\n\nFirst person to answer correctly wins!\n⏰ You have **45 seconds**!",
            color=0xFFFF00
        )
        
        event_msg = await context.send(embed=embed)
        
        # Track the event
        self.active_events[context.channel.id] = {
            'answer': answer.lower(),
            'start_time': time.time(),
            'tier': 2,
            'question': question
        }
        
        # Wait for 45 seconds
        await asyncio.sleep(45)
        
        # Check if event is still active (no winner)
        if context.channel.id in self.active_events:
            del self.active_events[context.channel.id]
            timeout_embed = discord.Embed(
                title="⏰ Event Timeout",
                description=f"Nobody answered correctly in time!\nThe answer was: **{answer}**",
                color=0xFF0000
            )
            await context.send(embed=timeout_embed)

    async def tier3Event(self, context):
        """
        Runs a Tier 3 event.
        A Tier 3 event is a challenging puzzle or brain teaser.
        The reward is a Tier 3 reward.
        """
        
        if context.channel.id in self.active_events:
            return  # Event already running in this channel
        
        event_type = random.randint(0, 3)
        
        match event_type:
            # Complex calculation
            case 0:
                a, b, c, d = random.randint(3, 12), random.randint(2, 8), random.randint(1, 5), random.randint(1, 10)
                answer = str((a * b) - (c * d))
                question = f"Calculate: ({a} × {b}) - ({c} × {d})"
                
            # Logic puzzle
            case 1:
                puzzles = [
                    ("I am a three-digit number. My tens digit is 5 more than my ones digit. My hundreds digit is 8 less than my tens digit. What number am I?", "194"),
                    ("A man lives on the 20th floor. Every morning he takes the elevator down to the ground floor. When he comes home, he takes the elevator to the 10th floor and walks the rest (unless it's raining). Why?", "short"),
                    ("What comes once in a minute, twice in a moment, but never in a thousand years?", "m"),
                    ("If today is Monday, what day will it be in 100 days?", "tuesday")
                ]
                puzzle_data = random.choice(puzzles)
                question = puzzle_data[0]
                answer = puzzle_data[1]
                
            # Pattern recognition
            case 2:
                patterns = [
                    ("A, C, F, J, O, ?", "u"),
                    ("2, 6, 12, 20, 30, ?", "42"),
                    ("Z, Y, X, W, V, ?", "u"),
                    ("1, 1, 2, 3, 5, 8, ?", "13")
                ]
                pattern_data = random.choice(patterns)
                question = f"What comes next in this pattern: {pattern_data[0]}"
                answer = pattern_data[1]
                
            # Word puzzle
            case 3:
                word_puzzles = [
                    ("What 8-letter word has only one vowel?", "strength"),
                    ("What word becomes shorter when you add two letters to it?", "short"),
                    ("What word is spelled the same forwards and backwards?", "racecar"),
                    ("What 5-letter word becomes shorter when you add 'er' to it?", "short")
                ]
                word_data = random.choice(word_puzzles)
                question = word_data[0]
                answer = word_data[1]
        
        # Create event embed
        embed = discord.Embed(
            title="🎉 Tier 3 Event Started!",
            description=f"**{question}**\n\nFirst person to answer correctly wins!\n⏰ You have **60 seconds**!",
            color=0xFF6600
        )
        
        event_msg = await context.send(embed=embed)
        
        # Track the event
        self.active_events[context.channel.id] = {
            'answer': answer.lower(),
            'start_time': time.time(),
            'tier': 3,
            'question': question
        }
        
        # Wait for 60 seconds
        await asyncio.sleep(60)
        
        # Check if event is still active (no winner)
        if context.channel.id in self.active_events:
            del self.active_events[context.channel.id]
            timeout_embed = discord.Embed(
                title="⏰ Event Timeout",
                description=f"Nobody answered correctly in time!\nThe answer was: **{answer}**",
                color=0xFF0000
            )
            await context.send(embed=timeout_embed)

    async def start_random_event(self, context):
        """Start a random event in the specified channel"""
        # 50% tier 1, # 35% tier 2, 15% tier 3
        tier = random.choices([1, 2, 3], weights=[50, 35, 15])[0]

        match tier:
            case 1:
                await self.tier1Event(context)
            case 2:
                await self.tier2Event(context)
            case 3:
                await self.tier3Event(context)

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     """Handle user responses to events"""
    #     if message.author.bot:
    #         return
        
    #     if message.channel.id not in self.active_events:
    #         return
        
    #     event_data = self.active_events[message.channel.id]
    #     user_answer = message.content.lower().strip()
        
    #     # Check if the answer is correct
    #     if user_answer == event_data['answer']:
    #         # Winner!
    #         del self.active_events[message.channel.id]
            
    #         # Create winner embed
    #         winner_embed = discord.Embed(
    #             title="🎉 Winner!",
    #             description=f"**{message.author.mention}** got it right!\nAnswer: **{event_data['answer']}**",
    #             color=0x00FF00
    #         )
    #         await message.channel.send(embed=winner_embed)
            
    #         # Give reward based on tier
    #         tier = event_data['tier']
    #         match tier:
    #             case 1:
    #                 await self.tier1Reward(message)
    #             case 2:
    #                 await self.tier2Reward(message)
    #             case 3:
    #                 await self.tier3Reward(message)

     
    # @commands.command(
    #     help = f"Event Information",
    #     description = EVENT_INFO,
    # )
    # @commands.cooldown(3, 10, commands.BucketType.user)
    # async def eventinfo(self, message):
    #     await message.send(embed=basicMsg(description=EVENT_INFO))

    # @commands.command(
    #     help="Start a random event",
    #     description="Starts a random event in the current channel"
    # )
    # @commands.cooldown(1, 60, commands.BucketType.channel)
    # async def startevent(self, ctx):
    #     """Start a random event in the current channel"""
    #     if ctx.channel.id in self.active_events:
    #         await ctx.send("⚠️ An event is already running in this channel!")
    #         return
        
    #     await self.start_random_event(ctx)

    # @commands.command(
    #     help="Check active events",
    #     description="Shows information about currently running events"
    # )
    # async def activevents(self, ctx):
    #     """Show active events"""
    #     if not self.active_events:
    #         embed = discord.Embed(
    #             title="Active Events",
    #             description="No events are currently running.",
    #             color=0x808080
    #         )
    #         await ctx.send(embed=embed)
    #         return
        
    #     event_list = []
    #     for channel_id, event_data in self.active_events.items():
    #         channel = self.bot.get_channel(channel_id)
    #         time_left = int(event_data['start_time'] + (30 if event_data['tier'] == 1 else 45 if event_data['tier'] == 2 else 60) - time.time())
    #         if time_left > 0:
    #             event_list.append(f"**{channel.name}** - Tier {event_data['tier']} ({time_left}s left)")
        
    #     if not event_list:
    #         description = "No events are currently running."
    #     else:
    #         description = "\n".join(event_list)
        
    #     embed = discord.Embed(
    #         title="Active Events",
    #         description=description,
    #         color=0x00FFFF
    #     )
    #     await ctx.send(embed=embed)

    # @commands.command(
    #     help="Start a specific tier event",
    #     description="Start an event of a specific tier (1, 2, or 3)"
    # )
    # @commands.cooldown(1, 120, commands.BucketType.channel)
    # async def starteventtier(self, ctx, tier: int):
    #     """Start a specific tier event"""
    #     if ctx.channel.id in self.active_events:
    #         await ctx.send("⚠️ An event is already running in this channel!")
    #         return
        
    #     if tier not in [1, 2, 3]:
    #         await ctx.send("❌ Invalid tier! Please use 1, 2, or 3.")
    #         return
        
    #     match tier:
    #         case 1:
    #             await self.tier1Event(ctx.channel)
    #         case 2:
    #             await self.tier2Event(ctx.channel)
    #         case 3:
    #             await self.tier3Event(ctx.channel)

async def setup(bot):
    await bot.add_cog(EventsCog(bot))