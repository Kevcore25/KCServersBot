import discord
from discord.ext import commands
from calculatefuncs import *
from games import GoFish

GOFISH_DESC = f"""*This version of GoFish is missing some minor features from the original.*
GoFish is a unique card game where you attempt to get more books (4 of the same number) than the bot; however, you may only guess a number from your deck. 
If the bot has the number you guessed, you gain the bot's cards of that number and you get to guess again.
Otherwise, you gain a card and it is the bot's turn, and it tries to guess your deck as well.

Payout: `{numStr(40 * calcInflation())} Credits`
Cost: `{numStr(15 * calcInflation())} Credits` (You can play even with negative balances)

The bot's algorithm is very simple and easy to predict, making this game easy to win if you know the right strategy.
Essentially, the bot saves the numbers you guess and prioritizes on guessing them when possible, otherwise it will simply guess a random number from its deck.
"""


class CardGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def msginput(self, ctx: discord.Message, text: str | None, timeout: int = 60) -> str:
        try:
            if text is not None: await ctx.send(text)
            ui = await self.bot.wait_for("message", check=lambda msg: msg.author == ctx.author, timeout=timeout)
            return str(ui.content)
        except TimeoutError:
            await ctx.send("You took too long to respond!")
        finally:
            await ui.delete()

    @commands.command(
        help = 'Play GoFish with the bot on difficulty 1 (less = harder)',
        description = GOFISH_DESC
            
    )
    async def gofish(self, message):
        botDifficulty = 1

        u1 = User(message.author.id)
        u2 = User("bot2")
        game = GoFish(u1, u2)

        lose = 15 * calcInflation()
        u1.addBalance(credits=-lose)

        botKnowns = []

        txt = []

        msg = await message.send(embed=discord.Embed(
            title = "GoFish Game",
            description = "A simple GoFish game, where you try to get the most decks by guessing what the bot has!",
            color = 0xFF00FF
        ))

        async def edit(text: str):
            embed = discord.Embed(
                title = "GoFish Game",
                description = f"""Your cards: {', '.join(str(i) for i in game.players[u1])}\n\nYour books: {', '.join(str(i) for i in sorted(game.playersFullCards[u1]))}\nBot books: {', '.join(str(i) for i in sorted(game.playersFullCards[u2]))}\n\n{text}""",
                color = 0xFF00FF
            )
            await msg.edit(embed=embed)

        async def bot():
            """BOT AI"""
            got = False
            # Ask a user 
            cards = game.players[u2]
            for c in cards:
                if c in botKnowns:
                    if random.randint(1, botDifficulty):
                        gt, picked = game.ask_user(u2, c)
                        if gt > 0:
                            got = True                        
                            txt.append(f"Bot turn!\nBot asked {c} and got {gt} cards from you!")
                        else:
                            txt.append(f"Bot turn!\nBot asked {c} and you say \"GO FISH\" so it picked up a card")
                            # Show if right
                            if c == picked:
                                txt.append(f"Bot got a {c} card!")

                        botKnowns.remove(c)
                        break
            else:
                # Guess a random card
                try:
                    randomC = random.choice(cards)

                except IndexError:
                    game.get_from_deck(u2, random.choice(game.totalCards))
                    randomC = random.choice(cards)

                gt, c = game.ask_user(u2, randomC)
                if gt > 0:
                    got = True
                    txt.append(f"Bot asked {randomC} randomly and got {gt} cards from you!")
                else:
                    txt.append(f"Bot turn!\nBot asked {randomC} and you say \"GO FISH\" so it picked up a card")

            # Determine full cards
            d = game.determine_full_card(u2)
            if d != False:
                txt.append(f"Bot got a full deck of {d}")

            # Continue
            if got:
                await bot()

        cards = game.players[u1]

        async def determine():
            if len(game.totalCards) <= 0:
                txt.append("Game over!")
                if len(game.playersFullCards[u1]) > len(game.playersFullCards[u2]):

                    # Add temporary credit gain
                    credits = calcCredit(40, u1) * calcInflation()
                    
                    u1.addBalance(credits=credits)

                    txt.append(f"Player won! You gained `{numStr(credits)} credits!` (Net total of `{numStr(credits - lose)}`)")
                else:
                    txt.append(f"Bot won! (You gained a net total of `{numStr(-lose)} Credits`)")
                return True
            else:
                return False

        while True:
            try:
                if await determine(): break

                cards.sort()

                if len(cards) == 0:
                    game.get_from_deck(u1, random.choice(game.totalCards))

                txt.append("Your turn!")
                # Edit messsage
                await edit('\n'.join(txt))
                txt = []
                card = await self.msginput(message, None)

                if card.isdigit():
                    card = int(card)
                elif card.lower() == "exit":
                    txt.append("Exited GoFish game")
                    return
                else:
                    txt.append("You must provide an integer! Type exit to exit")
                    continue

                if card not in cards:
                    txt.append("You must choose a card from your deck!")
                    continue

                # The bot sees it so append
                if card not in botKnowns: botKnowns.append(card)
                
                #game.ask_user(u1, card)
                got, c = game.ask_user(u1, card)
                if got > 0:
                    txt.append(f"You asked {card} and got {got} cards from the bot!")
                else:
                    txt.append(f"You asked {card} and the bot says \"GO FISH\" so you picked up a {c}")

                d = game.determine_full_card(u1)
                if d != False:
                    txt.append(f"You got a full deck of {d}!")

                # Continue
                if got > 0:
                    continue
                
                if await determine(): break
                
                # Bot 
                await bot()
            except Exception as e:
                await edit(f"An error occurred! This shouldn't happen!\n{e}")

        await edit('\n'.join(txt))

