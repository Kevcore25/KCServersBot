from random import randint
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from users import User
import time
from cardgames import *

jackpot = True
       
class CrashGame:
    def __init__(self) -> None:
        self.multiplier = 1
        self.round = 0
        self.multipliers = [self.multiplier]


    def change_multiplier(self) -> float:
        """Change the multiplier and return the result"""

        # 10% time, -.2
        if randint(0,9) == 0:
            self.multiplier -= 0.2
        else:
            # self.multiplier += randint(5,15) / 100
            self.multiplier += randint(2,10) / 200 * self.round

        self.multiplier = round(self.multiplier, 3)
        
        self.multipliers.append(self.multiplier)

        return self.multiplier

    def determine_crash(self) -> bool:
        """Determines if the round will crash"""

        global jackpot

        if not jackpot:
            print("JP")
            if (randint(0,30) == 0 or self.multiplier >= 100) and self.round > 50:
                jackpot = True
                print("jackpot expired")
                return True # Crashes
            else:
                return False
        else:
            if randint(0,9) == 0 or self.multiplier >= 100:
                return True # Crashes
            else:
                return False
        
    def cash_out(self, amount: float) -> float:
        """Cashes out the current multiplier"""
        return round(amount * self.multiplier, 3)

    def next_round(self) -> dict:
        """Go to the next round. Returns False if crashed"""

        crashed = self.determine_crash()

        if not crashed:
            self.change_multiplier()

        self.round += 1

        return {"crashed": crashed, "multiplier": self.multiplier}

    def create_plot(self) -> plt:
        plot = plt
        xpoints = [i+1 for i in range(len(self.multiplier))]
        ypoints = []

        for m in self.multipliers:
            ypoints.append(m)

        X_Y_Spline = make_interp_spline(xpoints, ypoints)

        xpoints = np.linspace(min(xpoints), max(xpoints), 500)
        ypoints = X_Y_Spline(xpoints)

        plot.plot(xpoints, ypoints)

        return plot


def sample_crash_game(bet: float, cashOutAt: int = 10, delay: float = 1) -> float:
    """Play a sample game and return the cashed out"""
    from time import sleep

    print(f"Betting ${bet} and cashing out at round {cashOutAt}.")
    cg = CrashGame()

    #plot = cg.create_plot()
    plot = plt
    plot.xlabel("Round")
    plot.ylabel("Multiplier")

    plot.ion()
    plot.show()

    xpoints = [0]
    ypoints = [1]

    while True:
        print(cg.round)
        if cg.round == cashOutAt:
            print("Cashing out")
            won = cg.cash_out(bet)
            break

        round = cg.next_round()

        plot.title(f"Round {cg.round} | Multiplier: {round['multiplier']}x")
        if round['crashed']:
            won = 0
            print("CRASHED!")
            plot.title(f"Round {cg.round} | Multiplier: 0x")

            xpoints.append(cg.round)
            ypoints.append(0)

            plot.plot(xpoints, ypoints)
        
            plot.draw()
            plot.pause(0.01)
            break
            
        print(f"Round {cg.round} | Multiplier: {round['multiplier']}")


        xpoints.append(cg.round)
        ypoints.append(round['multiplier'])

        plot.plot(xpoints, ypoints)
    
            
        plot.draw()
        plot.pause(0.01)

        sleep(delay)


    print(f"You won ${won}!")
  

pickaxeMultipliers = {
    "basic": 1,
    "iron": 1.3,
    "gold": 1.2,
    "diamond": 1.5
}
swordDamage = {
    "basic": 4,
    "iron": 6,
    "gold": 5,
    "diamond": 8
}
armorDefense = {
    "basic": 16,
    "iron": 24,
    "gold": 20,
    "diamond": 32
}
shieldDefense = {
    "basic": 16,
    "iron": 24,
    "gold": 20,
    "diamond": 32
}

PLAYER_TIER_COSTS = {
    "basic": 0,
    "iron": 100,
    "gold": 80,
    "diamond": 500
}



class Players:
    def __init__(self, ID: str):
        ID = str(ID)
        self.ID = ID
        self.user = User(ID)
        self.fix_account()

    def fix_account(self):
        """Adds the players {} key to users"""

        data = self.user.getData()
        
        if "players" not in data:
            data = {	       
                "war": {
                    "time": 0,
                    "opponent": None,
                    "won": False
                },
                "mineDate": 0,
                "minerals": 500,
                "food": 100,
                "gold": 0,
                "defaults": {
                    "pickaxe": "basic",
                    "armor": "basic",
                    "shields": "basic",
                    "sword":"basic_sword"
                },
                "players": [
                    {"health": 20, "maxHealth": 20, "armor": "basic", "shields": "basic", "sword": "basic", "pickaxe": "basic"},
                    {"health": 20, "maxHealth": 20, "armor": "basic", "shields": "basic", "sword": "basic", "pickaxe": "basic"},
                    {"health": 20, "maxHealth": 20, "armor": "basic", "shields": "basic", "sword": "basic", "pickaxe": "basic"}
                ]
            }
            return self.user.setValue('players', data)


    def get_data(self, key: str = None):
        return self.user.getData().get("players") if key is None else self.user.getData().get("players").get(key)

    def save_data(self, data: dict):
        return self.user.setValue('players', data)

    def set_value(self, key: str, value):
        data = self.user.getData().get("players")
        data[key] = value
        return self.save_data(data)

    def change_value(self, key: str, value: float):
        data = self.user.getData().get("players")
        data[key] += value
        return self.save_data(data)

    def start_mine(self):
        """Begin the mining process"""
        return self.set_value("mineDate", int(time.time()))
        

    def finish_mine(self):
        """Obtain the resources from mining depending on pops"""
        minerals = self.get_data('minerals')
        food = self.get_data('food')
        gold = self.get_data('gold')
        players = self.get_data("players")


        gain = [0,0,0]
        for player in players:
            food += 50
            minerals += (100 * pickaxeMultipliers[player['pickaxe']])
            gold += (100 * pickaxeMultipliers[player['pickaxe']])

            gain[0] += (100 * pickaxeMultipliers[player['pickaxe']])
            gain[1] += (100 * pickaxeMultipliers[player['pickaxe']])
            gain[2] += 50

        self.set_value("food", food)
        self.set_value("minerals", minerals)
        self.set_value("gold", gold)

        self.set_value("mineDate", 0)

        return gain


    def mine(self) -> dict:
        """Start mining. If process is running, return that, else if process done, then give minerals"""

        mineDate = self.get_data("mineDate")

        if mineDate == 0:
            self.start_mine()

            return {"success": True, "text": "Mining started."}

        elif time.time() - mineDate > 4 * 60 * 60:
            m, g, f = self.finish_mine()
        
            return {"success": True, "text": f"Mining finished! Obtained:\n+{m} minerals\n+{g} gold\n+{f} food"}
        else:
            return {"success": False, "text": f"There is already a mining session started!\nCome back in {round((mineDate + 4 * 60 * 60 - time.time()) / 60)} minutes"}

    def get_overpop(self):

        players = self.get_data('players')

        result = 1
        if len(players) > 10:
            result = 1 + ( (10 - len(players)) / 100*15 )

        return round(result, 3)
    

    def create_pop(self):
        """Creates one pop with current upgrades. Does not remove resources"""

        players = self.get_data('players')

        players.append(
            {"health": 20, "maxHealth": 20, "armor": "basic", "shields": "basic", "sword": "basic_sword", "pickaxe": "basic"}
        )

        return self.set_value("players", players)
    
    def remove_pop(self):
        """Removes the last pop"""
        players = self.get_data('players')
        players.pop()

        return self.set_value("players", players)
    
    def set_default(self, armor: str, shields: str, sword: str, pickaxe: str):
        return self.set_value("defaults", {"armor": armor, "shields": shields, "sword": sword, "pickaxe": pickaxe})
    
    def upgrade_single(self, i: int):
        """Upgrades the loadout for one pop"""

        players = self.get_data('players')
        defaults = self.get_data('defaults')
        minerals = self.get_data('minerals')
        food = self.get_data('food')

        foodRemoving, mineralsRemoving = 0, 0

        p = players[i]
        mh = p['maxHealth']
        
        if (mh - p['health']) + foodRemoving <= food: 
            foodRemoving += mh - p['health']
            players[i]["health"] = mh

        for k in ("armor", "pickaxe", "shields"):
            if p[k] != defaults[k]:
                tier = defaults[k]

                cost = PLAYER_TIER_COSTS[tier]

                # Stop if going to be in debt
                if cost + mineralsRemoving > minerals: continue

                mineralsRemoving += cost

                players[i][k] = tier

        if p['sword'] != defaults['sword']:
            tier, weapon = defaults['sword'].split("_")

            cost = PLAYER_TIER_COSTS[tier]

            # Stop if going to be in debt
            if cost + mineralsRemoving <= minerals: 
                mineralsRemoving += cost

                players[i]["sword"] = defaults['sword']

        minerals -= mineralsRemoving
        food -= foodRemoving

        self.set_value("food", food)
        self.set_value("minerals", minerals)

        return self.set_value("players", players)


    def upgrade(self):
        """Upgrades loadouts for all pops. Removes resources"""

        players = self.get_data('players')
        defaults = self.get_data('defaults')
        minerals = self.get_data('minerals')
        food = self.get_data('food')

        foodRemoving, mineralsRemoving = 0, 0

        for i in range(len(players)):
            p = players[i]
            mh = p['maxHealth']
            
            if (mh - p['health']) + foodRemoving <= food: 
                foodRemoving += mh - p['health']
                players[i]["health"] = mh

            for k in ("armor", "pickaxe", "shields"):
                if p[k] != defaults[k]:
                    tier = defaults[k]

                    cost = PLAYER_TIER_COSTS[tier]

                    # Stop if going to be in debt
                    if cost + mineralsRemoving > minerals: continue

                    mineralsRemoving += cost

                    players[i][k] = tier

            if p['sword'] != defaults['sword']:
                tier, weapon = defaults['sword'].split("_")

                cost = PLAYER_TIER_COSTS[tier]

                # Stop if going to be in debt
                if cost + mineralsRemoving > minerals: continue

                mineralsRemoving += cost

                players[i]["sword"] = defaults['sword']

        minerals -= mineralsRemoving
        food -= foodRemoving

        self.set_value("food", food)
        self.set_value("minerals", minerals)

        return self.set_value("players", players)

BATTLEWIDTH = 5
class FightPlayer:
    def __init__(self, attacker: User, defender: User):
        self.attacker = attacker
        self.defender = defender

        self.atker = Players(attacker.ID)
        self.defer = Players(defender.ID)


    def calcFightStr(self, players: list):
        """Calculates the strength of a user's pops"""
        totalFightStr = 0
        for player in players:

            dmg = (swordDamage[player['sword'].split('_')[0]]) 
            hp = (player['health'] + player['armor'] + player['shields'])
            totalFightStr += round((dmg * hp) ** 0.75 - 25, 3)
        return totalFightStr

    def calcFightStr2(self, players: list):
        """Calculates the strength of a user's pops"""
        totalFightStr = 0
        for player in players:
            hpV = player['hpValues']
            dmg = (swordDamage[player['sword'].split('_')[0]]) 
            hp = (player['health'] + hpV[0] + hpV[1])
            totalFightStr += round((dmg * hp) ** 0.75, 3)

        return totalFightStr

    def attack(self, attacker: dict, defender: dict) -> tuple[int, int, int]:
        """Pop attacks another pop, and return defender value. For now, all weapon types do not give bonuses nor give debuffs"""

        weaponTier = attacker['sword'].split("_")[0]
        damage = swordDamage[weaponTier]

        # Shields, then armor, then health
        shields = defender['hpValues'][1]
        armor = defender['hpValues'][0]

        def calc(defender, damage, shields, armor):
            if shields > 0:
                shields -= damage

                if shields < 0:
                    overamt = shields + damage
                    shields = 0
                    calc(defender, overamt, shields, armor)

            elif armor > 0:
                armor -= damage

                if armor < 0:
                    overamt = armor + damage

                    armor = 0
                    calc(defender, overamt, shields, armor)
            else:
                defender["health"] -= damage

            if defender['health'] <= 0: 
                defender['health'] = 0
            
            return defender['health'], armor, shields

        return calc(defender, damage, shields, armor)

    def fight(self, atkerPlayers: dict, deferPlayers: dict):
        """Main function"""


        for i in range(BATTLEWIDTH):
            # Defenders attack Attackers first

            # DEFENDER TURN
            if len(deferPlayers) > i: 
                try:
                    tempi = i
                    h, a, s = self.attack(deferPlayers[tempi], atkerPlayers[tempi])
                except IndexError:
                    tempi = 0
                    if len(atkerPlayers) == 0: return atkerPlayers, deferPlayers
                    h, a, s = self.attack(deferPlayers[tempi], atkerPlayers[tempi])

                if h <= 0: 
                    del atkerPlayers[tempi]
                else:
                    atkerPlayers[tempi]['hpValues'][0] = a
                    atkerPlayers[tempi]['hpValues'][1] = s
            # ATTACKER TURN
            if len(atkerPlayers) > i: 
                try:
                    tempi = i
                    h, a, s = self.attack(atkerPlayers[tempi], deferPlayers[tempi])
                except IndexError:
                    tempi = 0
                    if len(deferPlayers) == 0: return atkerPlayers, deferPlayers
                    h, a, s = self.attack(atkerPlayers[tempi], deferPlayers[tempi])

                if h <= 0: 
                    del deferPlayers[tempi]
                else:
                    deferPlayers[tempi]['hpValues'][0] = a
                    deferPlayers[tempi]['hpValues'][1] = s

        return atkerPlayers, deferPlayers

    def main(self):
        atkerPlayers = self.atker.get_data('players')
        deferPlayers = self.defer.get_data('players')
        initatkamt = len(atkerPlayers)
        initdefamt = len(deferPlayers)

        # Add temp stats
        for i in range(len(atkerPlayers)):
            atkerPlayers[i]['hpValues'] = [
                armorDefense[atkerPlayers[i]['armor']],
                shieldDefense[atkerPlayers[i]['shields']]
            ]
        for i in range(len(deferPlayers)):
            deferPlayers[i]['hpValues'] = [
                armorDefense[deferPlayers[i]['armor']],
                shieldDefense[deferPlayers[i]['shields']]
            ]

        for turn in range(100):

            atkerPlayers, deferPlayers = self.fight(atkerPlayers, deferPlayers)

            astr = self.calcFightStr2(atkerPlayers)
            dstr = self.calcFightStr2(deferPlayers)
            
            time.sleep(0.3)

            print(f"Turn {turn}: Atk STR: {round(astr)} | Def STR: {round(dstr)}")

            if astr <= 0 or dstr <= 0:
                break

        # Clean up temporally values
         # Add temp stats
        for i in range(len(atkerPlayers)):
            del atkerPlayers[i]['hpValues']
        for i in range(len(deferPlayers)):
            del deferPlayers[i]['hpValues']

        print(f"User {self.atker.ID} lost {initatkamt - len(atkerPlayers)} players (Started with {initatkamt})")
        print(f"User {self.defer.ID} lost {initdefamt - len(deferPlayers)} players (Started with {initdefamt})")

if "__main__" in __name__:
    # fp = FightPlayer(User(1),User(623339767756750849))
    # fp.main()


    
    # print(fp.attack(
    #     {"health": 20, "maxHealth": 20, "armor": "basic", "shields": "basic", "sword": "basic", "pickaxe": "basic"},
    #     {"health": 20, "maxHealth": 20, "armor": "basic", "shields": "basic", "sword": "basic", "pickaxe": "basic"},

    # ))

    betamt = 1000
    cashout = 2

    #       Rounds: v

    #for c in range(10,101, 1):


    cashout = 1.5
    for c in range(10, 1000, 50):
        cashout = c/10    
        money = 10000

        won = 0
        for i in range(100000):
            money -= betamt
            cg = CrashGame()
            cg.multiplier = 0.75 #New
            while True:
                r = cg.next_round()
                #print(f"Multiplier {r['multiplier']}")
                if r["crashed"]:
                    break
                elif cashout <= r['multiplier']:
                    money += (betamt * r['multiplier'])
                    won += 1
                    break
            #if money < 0: break
                

        print(f"{cashout}x (value): {round(money / 5000, 1)} (Won {won} times)")


