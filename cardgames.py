# Deck for GO FISH
from users import User
import random

gofishDeck = []
for i in range(13):
    for j in range(4):
        gofishDeck.append(i+1)

class GoFish:
    def __init__(self, u1: User, u2: User):
        self.u1 = u1
        self.u2 = u2
    
        self.botKnowns = []
    
        self.players = {
            self.u1: [],
            self.u2: []
        }
    
        self.playersFullCards = {
            self.u1: [],
            self.u2: []
        }

        self.totalCards = gofishDeck.copy()

        for i in (u1, u2):
            self.generate_player_deck(i)
    
    def get_from_deck(self, user: User, card: int):

        randomCard = card

        if len(self.totalCards) > 0:
            self.totalCards.remove(randomCard)
            self.players[user].append(randomCard)
            return True
        else:
            return False



    def generate_player_deck(self, user: User):
        # Give 7 from deck
        for i in range(7):
            self.get_from_deck(user, random.choice(self.totalCards))

    def start(self):
        self.generate_player_deck(self.u1)
        self.generate_player_deck(self.u2)

    def card_in_cards(self, user: User, card: int):
        return self.players[user].count(card)
    
    def get_other_user(self, user: User):
        temp = list(self.players)
        temp.remove(user)
        otherUser = temp[0]
        return otherUser

    def give_card_to_other(self, user: User, card):
        otherUser = self.get_other_user(user)

        self.players[user].remove(card)
        self.players[otherUser].append(card)

    def ask_user(self, userAsking: User, card: int) -> int:
        otherUser = self.get_other_user(userAsking)

        count = self.card_in_cards(otherUser, card)
        
        if count > 0:
            for i in range(count):
                self.give_card_to_other(otherUser, card)
        else:
            # Pick up one card
            self.get_from_deck(userAsking, random.choice(self.totalCards))
        return count

    def determine_full_card(self, user: User):

        for i in tuple(set(self.players[user])):
            if self.players[user].count(i) >= 4:
                for j in range(4): self.players[user].remove(i)
                self.playersFullCards[user].append(i)
                return i
        
        return False



# Higher = easier
botDifficulty = 100
def example():
    print("playing a game with bot1 and bot2")

    u1 = User("bot1")
    u2 = User("bot2")
    game = GoFish(u1, u2)


    botKnowns = []

    def bot():
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
                    print(f"Bot asked {c} and got {gt} cards from you!")
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
            print(f"Bot asked {randomC} randomly and got {gt} cards from you!")

        # Determine full cards
        d = game.determine_full_card(u2)
        if d != False:
            print(f"Bot got a full deck of {d}. Current fulls: {game.playersFullCards[u2]}")

        # Continue
        if got:
            bot()

    cards = game.players[u1]


    def determine():
        if len(game.totalCards) <= 0:
            print("Game over!")
            if len(game.playersFullCards[u1]) > len(game.playersFullCards[u2]):
                print("Player won!")
            else:
                print("Bot won!")
            return True
        else:
            return False

    #print(game.players)

    while True:
        if determine(): break

        #print(game.players[u2])
        cards.sort()

        if len(cards) == 0:
            game.get_from_deck(u1, random.choice(game.totalCards))


        print(f"\nYour turn!\nYour cards: {cards}")
        card = input("Card: ")

        if card.isdigit():
            card = int(card)
        else:
            print("You must provide an integer!")
            continue

        if card not in cards:
            print("You must choose a card from your deck!")
            continue

        # The bot sees it so append
        if card not in botKnowns: botKnowns.append(card)
        
        #game.ask_user(u1, card)
        got = game.ask_user(u1, card)
        print(f"You asked {card} and got {got} cards from the bot!")

        d = game.determine_full_card(u1)
        if d != False:
            print(f"You got a full deck of {d}! Current fulls: {game.playersFullCards[u1]}")

        # Continue
        if got > 0:
            continue
        
        if determine(): break
        
        # Bot 
        print("Bot turn!")
        bot()

if "__main__" in __name__:
    example()