import discord
from discord.ext import commands
from calculatefuncs import *
from games import GoFish

class CardGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def msginput(self, ctx: discord.Message, text: str | None, timeout: int = 60) -> str:
        if text is not None: await ctx.send(text)
        ui = await self.bot.wait_for("message", check=lambda msg: msg.author == ctx.author, timeout=timeout)
        return str(ui.content)

    @commands.command(help = 'Play GoFish with the bot on difficulty 1 (less = harder)')
    async def gofish(self, message):
        botDifficulty = 1

        u1 = User(message.author.id)
        u2 = User("bot2")
        game = GoFish(u1, u2)


        botKnowns = []

        async def bot():
            """BOT AI"""
            got = False
            # Ask a user 
            cards = game.players[u2]
            for c in cards:
                if c in botKnowns:
                    if random.randint(1, botDifficulty):
                        gt = game.ask_user(u2, c)
                        if gt > 0:
                            got = True
                        botKnowns.remove(c)
                        await message.send(f"Bot turn! Bot asked {c} and got {gt} cards from you!")
                        break
            else:
                # Guess a random card
                try:
                    randomC = random.choice(cards)

                except IndexError:
                    game.get_from_deck(u2, random.choice(game.totalCards))
                    randomC = random.choice(cards)

                gt = game.ask_user(u2, randomC)
                if gt > 0:
                    got = True
                await message.send(f"Bot asked {randomC} randomly and got {gt} cards from you!")

            # Determine full cards
            d = game.determine_full_card(u2)
            if d != False:
                await message.send(f"Bot got a full deck of {d}. Current fulls: {game.playersFullCards[u2]}")

            # Continue
            if got:
                bot()

        cards = game.players[u1]


        async def determine():
            if len(game.totalCards) <= 0:
                await message.send("Game over!")
                if len(game.playersFullCards[u1]) > len(game.playersFullCards[u2]):

                    # Add temporary credit gain

                    credits = calcCredit(40, u1) * calcInflation()
                    
                    u1.addBalance(credits=credits)

                    await message.send(f"Player won! You gained `{credits} credits!`")
                else:
                    await message.send("Bot won!")
                return True
            else:
                return False

        #await message.send(game.players)

        while True:
            if await determine(): break

            #await message.send(game.players[u2])
            cards.sort()

            if len(cards) == 0:
                game.get_from_deck(u1, random.choice(game.totalCards))

            card = await self.msginput(message, f"Your turn!\nYour cards: {cards}\n\nCard to ask (input)...")


            if card.isdigit():
                card = int(card)
            elif card.lower() == "exit":
                await message.send("Exited GoFish game")
                return
            else:
                await message.send("You must provide an integer! Type exit to exit")
                continue

            if card not in cards:
                await message.send("You must choose a card from your deck!")
                continue

            # The bot sees it so append
            if card not in botKnowns: botKnowns.append(card)
            
            #game.ask_user(u1, card)
            got = game.ask_user(u1, card)
            await message.send(f"You asked {card} and got {got} cards from the bot!")

            d = game.determine_full_card(u1)
            if d != False:
                await message.send(f"You got a full deck of {d}! Current fulls: {game.playersFullCards[u1]}")

            # Continue
            if got > 0:
                continue
            
            if await determine(): break
            
            # Bot 
            await bot()
        

