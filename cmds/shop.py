import discord
from discord.ext import commands
from calculatefuncs import *

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
    @commands.command(
        help = "Buy an item from the shop",
        description = f"Notice: For this command, item ID can contain spaces without the requirement of quotation marks.\nThe last argument can be a number, which specifies how much you want to buy. Therefore, the command format is:\n`{prefix}buy <Item ID> [amount to buy]`",
        aliases = ['purchase'],
    )
    async def buy(self, message, *itemID): # command is an argument    
        # Detect amount

        try:
            amt: str = itemID[-1]
            if amt.isdigit():
                amount = int(amt)
                itemID = itemID[:-1]
            else:
                amount = 1
        except IndexError:
            amount = 1

        if itemID is None: 
            await message.send(embed=errorMsg("Item ID is not specified"))
            return

        with open("shop.json", 'r') as f:
            shopitems = json.load(f)

        # Title
        itemID = str(' '.join(itemID)).title()

        if itemID not in shopitems:
            await message.send(embed=errorMsg(f"Item ID ({itemID}) is not vaild"))
        else:
            item = shopitems[itemID]
            u = User(message.author.id, doNotCheck=True) # Prevent the case of data corruption

            creds, unity, gems = u.getData("credits"), u.getData("unity"), u.getData("gems")

            # Check for balance
            if (
                (creds >= item['credits'] or item['credits'] <= 0) and
                (unity >= item['unity'] or item['unity'] <= 0) and
                (gems  >= item['gems'] or item['gems'] <= 0)
            ):
                items: list = u.getData('items')

                itemCount = items[itemID]['count'] if itemID in items else 0

                # Max limit acheived
                if itemCount >= item['limit']:
                    await message.send(embed=errorMsg("Item limit reached!"))
                    return
                
                # Get initial stock
                with open('shopstock.json', 'r') as f:
                    stocks = json.load(f)

                if itemID not in stocks:
                    stocks[itemID] = 0

                stock = item['stock'] - stocks[itemID]

                # Out of stock
                if stock <= 0:
                    await message.send(embed=errorMsg("Item is out of stock!"))
                    return
                
                # Append Items
                if itemID not in items:
                    items[itemID] = {
                        "expires": [],
                        "data": {},
                        "count": 0
                    }

                for bought in range(amount):
                    item = shopitems[itemID]

                    # Out of stock
                    itemCount = items[itemID]['count']
                    if stock <= 0 or itemCount >= item['limit']:
                        bought -= 1
                        break
            
                    items[itemID]['count'] += 1

                    if item['expiry'] != -1:
                        items[itemID]['expires'].append(int(time.time() + item['expiry']))
                    else:
                        items[itemID]['expires'].append(-1)

    
                    stock -= 1

                # bought times
                bought += 1

                # Remove balance
                u.addBalance(credits = -round(item['credits'] * bought, 5), unity = -round(item['unity'] * bought, 5), gems = -round(item["gems"] * bought))

                # Add item
                u.setValue("items", items)

                # Set stock
                stocks[itemID] += bought
                with open('shopstock.json', 'w') as f:
                    stocks = json.dump(stocks, f, indent = 4)

                await message.send(embed=successMsg(title="Item bought!", description=f"Successfully bought `{bought}` `{itemID}` for `{item['credits'] * bought} Credits`, `{item['unity'] * bought} Unity`, and `{item['gems'] * bought} Gems`"))

            else:
                await message.send(embed=errorMsg(f"You do not have enough currencies to buy this item!\n## Tips:{WAYS_TO_EARN['credits']}"))

    @commands.command(
        help = "View shop items",
    )
    async def shop(self, message): # command is an argument
        embed = discord.Embed(title="Shop Items", color=0xFF00FF)

        with open("shop.json", 'r') as f:
            shopitems = json.load(f)

        for id in shopitems:
            costs = []
            item = shopitems[id]
            inflation = calcInflation()
            if item['credits'] != 0: costs.append(f"{round(item['credits'] * inflation, 2)} Credits")
            if item['unity'] != 0: costs.append(f"{item['unity']} Unity")
            if item['gems'] != 0: costs.append(f"{item['gems']} Gems")

            if len(costs) > 1:
                costsTxt = ", ".join(costs[:-1]) + ", and " + costs[-1] 
            elif len(costs) == 1:
                costsTxt = costs[0]
            else:
                costsTxt = "Free"

            # Get stock
            with open('shopstock.json', 'r') as f:
                stocks = json.load(f)

            if id in stocks:
                stock = item['stock'] - stocks[id]
            else:
                stock = item['stock']

            embed.add_field(name=f"{id} ({costsTxt})", value=item['description'] + f"\n*{('Expires after `' + time_format(item['expiry']) + '`') if item['expiry'] != -1 else 'Never expires'} | Limit: `{item['limit']}` | Stock: `{get_prefix(stock, 0)}`*", inline=False)

        embed.set_footer(text="All items expire after a reset, despite if it states \"Never expires\"")
        await message.send(embed=embed)
