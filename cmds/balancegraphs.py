import discord
from discord.ext import commands
from calculatefuncs import *
import matplotlib.pyplot as plt
import datetime
import bisect
import matplotlib.dates as mdates

TIME_DURATION_UNITS = (
    ('month', 60*60*24*30),
    ('week', 60*60*24*7),
    ('day', 60*60*24),
    ('hour', 60*60),
    ('min', 60),
    ('sec', 1)
)

def human_time_duration(seconds):
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{} {}{}'.format(amount, unit, "" if amount == 1 else "s"))
    return ', '.join(parts)

class BalanceGraphs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help = f"Graph your balance changes",
        description = f"""Format: {prefix}oldgraphbalance <user> <timeframe>""",
        aliases = ['ogb', 'oldgraphbal', 'oldbalgraph', 'obg', 'oldbalancegraph']
    )
    @commands.cooldown(3, 10, commands.BucketType.user) 
    async def oldgraphbalance(self, message: discord.Message, user: discord.Member = None, *, timeframe: str = "1d"):
        # Timeframe. Use KCTimeFrame Format
        timeframe = timeframe.lower().replace(",", " ")

        # Total is in Seconds
        total = 0

        inttemp = []
        skip = False
        for i in range(len(timeframe)):
            t = timeframe[i]

            if t == " ": 
                skip = False
            elif skip:
                continue

            # Is a digit. Record it until a letter is seen
            if t.isdigit():
                inttemp.append(t)
            elif t == " ": 
                continue
            # not a digit. Check for what, like day or month
            else:
                # If empty, just skip
                if len(inttemp) == 0: continue

                timeframetemp = int("".join(inttemp))

                if t == "d": # Days
                    timeframetemp *= (60 * 60 * 24)
                elif t == "h": # Hours
                    timeframetemp *= (60 * 60) 
                elif t == "m": # Either: minute (more likely so fallback) or month
                    # Month. Add a space in case of index errors
                    if (timeframe + " ")[i+1] == "o":
                        timeframetemp = int(timeframetemp * (60 * 60 * 24 * 30.5))
                    else:
                        timeframetemp *= (60)
                elif t == "w": # Weeks
                    timeframetemp *= (60 * 60 * 24 * 7)
                elif t == "y":
                    timeframetemp *= (60 * 60 * 24 * 365)
                elif t == "s": # Seconds. Nothing really should happen
                    pass
                
                total += timeframetemp
                inttemp = []
                skip = True # Skip until next space
        
        if user is None:
            user = message.author
            userid = message.author.id
        else:
            userid = user.id
            if userid == self.bot.user.id:
                userid = 'main'

        # Blocked by user
        if not User(userid).getData('settings').get("publicity", True): 
            await message.send(embed=errorMsg("The specified user has chosen to hide their profile details!"))
            return

        # Requires Account Viewer for not self
        if user.id != message.author.id:
            authoruser = User(message.author.id)
            if authoruser.item_exists("Account Viewer"):
                authoruser.delete_item("Account Viewer")
            else:
                await message.send(embed=errorMsg("You need the Account Viewer item to view other people's balances!"))
                return
            
        # Initialize a list to store the balances
        balances = []
        xstrs = []

        try:
            with open(os.path.join("balanceLogs", str(userid)), 'rb') as f:
                # Move the pointer to the end of the file
                f.seek(0, 2)
                # Get the file size
                size = f.tell()

                tf = "Unknown"

                # Start from the end of the file
                for i in range(size - 1, -1, -1):
                    f.seek(i)
                    # Read a byte
                    char = f.read(1)
                    # If it's a newline character and we haven't reached the end of file
                    if char == b'\n' and i < size - 1:
                        # Add the line to the list
                        ln = f.readline().decode().rstrip()
                        try:
                            t = int(ln.split(" ")[0])
                        except ValueError: continue

                        if (time.time() - t) > total:
                            break

                        bal = ln.split(" ")[1]
                        balances.append(float(bal))

                        # For string as X value
                        mst = datetime.datetime.fromtimestamp(t, datetime.timezone.utc) - datetime.timedelta(hours=7)

                        # Timeframes. Notice: Again, too much data will override it and it will not be shown
                        # For day (> 1 day) (Probably not shown)
                        if total > (60 * 60 * 24):
                            xstrs.append(mst.strftime("%d"))
                            tf = "Days"
                        else:
                            # For hour time (within a reasonable amount, like <1 day)
                            try:
                                xstrs.append(mst.strftime("%-H:%M"))
                            except ValueError:
                                xstrs.append(mst.strftime("%#H:%M"))
                            tf = "Hourtime"
        except FileNotFoundError:
            await message.send(embed=errorMsg("No balance logs have been recorded!"))
            return 
        
        # If there is only 1 item in the list, nothing will be graphed, so add the same value to the balance.
        if len(balances) == 1:
            balances = balances * 2

        balances.reverse()

        xvalues = [i for i in range(len(balances))]

        xstrs.reverse()
        # If too much data then don't show on graph
        if len(xstrs) < 30:
            plt.xticks(xvalues, xstrs)
        else:
            tf = "Indexes"

        # Create plot
        plt.xlabel(f"Timeframe ({tf})")
        plt.ylabel("Credit Balance")




        plt.title(f"{user.display_name}'s balance changes since {human_time_duration(total)} ago")

        # Slope color
        try:
            first, last = balances[0], balances[-1]
            if first > last: color = 'red'
            elif first < last: color = 'green'
            else: color = 'gray'
        except IndexError:
            color = 'gray'

        plt.plot(xvalues, balances, color=color)

        plt.savefig(f"temp/bal{userid}.png")
        plt.clf()

        file = discord.File(f"temp/bal{userid}.png", filename=f"balanceGraph.png")
        embed = discord.Embed(title="Balance Graph", color=0xFF00FF)
        embed.set_image(url=f"attachment://balanceGraph.png")

        await message.send(file=file, embed=embed)

        os.remove(f"temp/bal{userid}.png")


    """
    This is a new experimental balance graph. 
    The old one graphs everytime the balance changes. However, this one graphs every x min
    Therefore, it is more accurate to the real-world graphs, where you can see the balances every x hour for eaxample.

    How does it work?
    Initially, it reads the entire balance log up to the specified date. It saves it into a list.
    Then, it will begin to plot the balance every x specified by the time.
    There will be 100 points, so x can be calculated by every time/100.
    Let's go with an example.
    Suppose the balance changed at time 12, 35 and 95, with the balance being 50, 100 and 120 respectively.
    The user wanted up to time 30. 
    It will begin to record the y value as 120 for x = 100, x = 99... x = 95
    Then, at x = 94, it will record the balance being 100 up to x = 35
    Now, up to x = 0, the y value will be 12 because that is the last value.
    If the user wanted up to time 0, because there aren't any other recorded data, we will assume the balance to be 0
    So y in x = [0, 11] will be 0.
    """
    @commands.command(
        help = f"Graph your balance changes",
        description = f"""Format: {prefix}graphbalance <user> [timeframe] [precision]
    user: Member of the user. This can be a @mention
    timeframe: The timeframe for the graph. This can be expressed in words, such as "3 days ago" or simply just "3d" or "34s"
    precision: A percentage from 1-100 for the precision of points. More points mean more precision. By default, this is 1%
    Notice: If the data is too large, precision will be limited to prevent long executions
    """,
        aliases = ['gb', 'balgraph', 'graphbal', 'bg', 'balancegraph']
    )
    @commands.cooldown(2, 10, commands.BucketType.user) 
    async def graphbalance(self, message: discord.Message, user: discord.Member = None, *, timeframe: str = "1d"):
        # Parameter for points
        t = timeframe.split(' ')
        if len(t) > 1 and t[-1].replace(".", '').isdigit():
            precision = float(t[-1])
        else:
            precision = 1


        # Timeframe. Use KCTimeFrame Format
        timeframe = timeframe.lower().replace(",", " ")

        # Total is in Seconds
        total = 0

        inttemp = []
        skip = False
        for i in range(len(timeframe)):
            t = timeframe[i]

            if t == " ": 
                skip = False
            elif skip:
                continue

            # Is a digit. Record it until a letter is seen
            if t.isdigit():
                inttemp.append(t)
            elif t == " ": 
                continue
            # not a digit. Check for what, like day or month
            else:
                # If empty, just skip
                if len(inttemp) == 0: continue

                timeframetemp = int("".join(inttemp))

                if t == "d": # Days
                    timeframetemp *= (60 * 60 * 24)
                elif t == "h": # Hours
                    timeframetemp *= (60 * 60) 
                elif t == "m": # Either: minute (more likely so fallback) or month
                    # Month. Add a space in case of index errors
                    if (timeframe + " ")[i+1] == "o":
                        timeframetemp = int(timeframetemp * (60 * 60 * 24 * 30.5))
                    else:
                        timeframetemp *= (60)
                elif t == "w": # Weeks
                    timeframetemp *= (60 * 60 * 24 * 7)
                elif t == "y":
                    timeframetemp *= (60 * 60 * 24 * 365)
                elif t == "s": # Seconds. Nothing really should happen
                    pass
                
                total += timeframetemp
                inttemp = []
                skip = True # Skip until next space
        
        if user is None:
            user = message.author
            userid = message.author.id
        else:
            userid = user.id
            if userid == self.bot.user.id:
                userid = 'main'

        # Blocked by user
        if not User(userid).getData('settings').get("publicity", True): 
            await message.send(embed=errorMsg("The specified user has chosen to hide their profile details!"))
            return

        # Requires Account Viewer for not self
        if user.id != message.author.id:
            authoruser = User(message.author.id)
            if authoruser.item_exists("Account Viewer"):
                authoruser.delete_item("Account Viewer")
            else:
                await message.send(embed=errorMsg("You need the Account Viewer item to view other people's balances!"))
                return

        # Initialize a list to store the balances
        balances = []
        data = []
        try:
            with open(os.path.join("balanceLogs", str(userid)), 'rb') as f:
                # Move the pointer to the end of the file
                f.seek(0, 2)
                # Get the file size
                size = f.tell()
                # Start from the end of the file
                toBreak = False
                for i in range(size - 1, -1, -1):
                    if toBreak: break
                    f.seek(i)
                    # Read a byte
                    char = f.read(1)
                    # If it's a newline character and we haven't reached the end of file
                    if char == b'\n' and i < size - 1:
                        # Add the line to the list
                        ln = f.readline().decode().rstrip()
                        try:
                            t = int(ln.split(" ")[0])
                        except ValueError: continue

                        if (time.time() - t) > total:
                            toBreak = True

                        bal = ln.split(" ")[1]
                        recordedTime = ln.split(" ")[0]
                        # print(recordedTime) 

                        # balances.append(float(bal))
                        # recordedTimes.append(int(recordedTime))
        
                        try:
                            # Convert epoch time to datetime (UTC if needed, use utcfromtimestamp)
                            dt = datetime.datetime.fromtimestamp(int(recordedTime))
                            balance = float(bal)
                            data.append((dt, balance))
                        except ValueError:
                            continue  # Skip lines with invalid numbers
            
        except FileNotFoundError:
            await message.send(embed=errorMsg("No balance logs have been recorded!"))
            return 
    
        data.sort(key=lambda x: x[0])
        def generate_time_points(end_time, window_seconds, interval_seconds):
            """Generates timestamps at intervals within the time window"""

            # Align end_time to the nearest interval
            aligned_timestamp = (int(end_time.timestamp()) // interval_seconds) * interval_seconds
            aligned_end = datetime.datetime.fromtimestamp(aligned_timestamp)
            
            window_delta = datetime.timedelta(seconds=window_seconds)
            interval_delta = datetime.timedelta(seconds=interval_seconds)
            
            time_points = []
            current_time = aligned_end
            while current_time >= (aligned_end - window_delta):
                time_points.append(current_time)
                current_time -= interval_delta
            return time_points[::-1]  # Return oldest first for better bisect behavior

        # Parse data and extract timestamps/balances
        timestamps = [dt for dt, bal in data]
        balances = [bal for dt, bal in data]

        # Init variables for time periods
        totalsec = total       # Total time window to visualize (e.g., 24*3600=24h)

        # If data is too much, do not use that much precision
        maxData = 500
        dataAmt = len(data)
        print(len(data))
        if dataAmt > maxData:
            print("Uh oh, overflow!")
            # Should not exceed maxData points
            # 10000 = totalsec * precision / 100
            # 10000 x 100 / totalsec = precsision

            maxprecision = maxData * 100 * maxData / totalsec
            
            if precision > maxprecision:
                precision = maxprecision

        if precision is None:
            amtOfPoints = 20
        else:
            amtOfPoints = round(totalsec * (precision / 100))
        step = total // amtOfPoints

        # Generate target time points for the graph
        end_time = datetime.datetime.now()
        graph_times = generate_time_points(end_time, totalsec, step)

        # Find the balance at each target time
        graph_balances = []
        for t in graph_times:
            idx = bisect.bisect_right(timestamps, t) - 1
            graph_balances.append(balances[idx] if idx >= 0 else 0.0)

        # Slope color
        try:
            first, last = graph_balances[0], graph_balances[-1]
            if first > last: color = 'red'
            elif first < last: color = 'green'
            else: color = 'gray'
        except IndexError:
            color = 'gray'
        # Plotting
        plt.figure(figsize=(12, 6))
        plt.plot(graph_times, graph_balances, linestyle='-', color=color)
        plt.title(f'Balance Over {totalsec//3600}h (Sampled Every {step//3600}h with {round(precision, 5)}% precision*)')
        plt.xlabel('Time')
        plt.ylabel('Balance')

        # Format x-axis based on time window
        time_format = '%m/%d %H:%M' if totalsec <= 86400 else '%m/%d'
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(time_format))
        plt.gcf().autofmt_xdate()
        plt.grid(True)
        plt.tight_layout()

        plt.savefig(f"temp/bal{userid}.png")
        plt.clf()

        file = discord.File(f"temp/bal{userid}.png", filename=f"balanceGraph.png")
        embed = discord.Embed(title="Balance Graph", color=0xFF00FF)
        embed.set_image(url=f"attachment://balanceGraph.png")

        await message.send(file=file, embed=embed)

        os.remove(f"temp/bal{userid}.png")


    @commands.command(
        help = f"Graph your score changes",
        description = f"""This command approximates the score you had based on index location (instead of time)
It is an approximation, so the actual value may be higher than expected. 
This is due to the following score reasons being uncalculatable:
1. Leaderboard ranking
Unfortunately, this is hard to approximate. 
Reading all the user's balance log is very resource intensive, so instead, the alghorithm will use a different method.
This method compares the slope of the current average credits to the default (50) using your current credits to the oldest log as x values.
Then for each log, if your credits is above the average credits by 20% at that point, then it assigns a LB score of 7.5, or else it will be 2.5 if it is below 15%, or else a LB score of 5 otherwise.
You may notice jumps in the graph due to this calculation.

2. KCash Exchanged
The KCash Exchanged is almost impossible to detect. It is not stored into the balance logs of a user (as of V.5.4).
Therefore, it can't give a good approximation on this score reason.
For now, the KCash exchanged is completely ignored unless it is the last point.
It may be possible to find the point where the difference is exactly the amount of KCash Exchanged, but once the user exchanges multiple times, then this method also will not work.
Ultimately, it is impossible to detect KCash exchanged for this balance graph.
""",
        aliases = ['sgb', 'gbs', 'graphbalancescore', 'bgs', 'balancegraphscore', 'scorebalancegraph']
    )
    @commands.cooldown(3, 10, commands.BucketType.user) 
    async def scoregraphbalance(self, message: discord.Message, user: discord.Member = None):
        if user is None:
            user = message.author
            userid = message.author.id
        else:
            userid = user.id
            if userid == self.bot.user.id:
                userid = 'main'

        # Blocked by user
        if not User(userid).getData('settings').get("publicity", True): 
            await message.send(embed=errorMsg("The specified user has chosen to hide their profile details!"))
            return

        # Requires Account Viewer for not self
        if user.id != message.author.id:
            authoruser = User(message.author.id)
            if authoruser.item_exists("Account Viewer"):
                authoruser.delete_item("Account Viewer")
            else:
                await message.send(embed=errorMsg("You need the Account Viewer item to view other people's balances!"))
                return
            
        # Initialize a list to store the balances
        balances = []
        xstrs = []


        totalCred = 0
        totalUnity = 0
        logs = 0

        # Calculate slope of LB score approximation
        # slope = y2 - y1 / (x2 - x1)
        # where y = avg credits and x = index
        
        # Get number of lines
        with open(os.path.join("balanceLogs", str(userid)), 'r') as f:
            lines = len(f.readlines())

        avgCredits = calcAvgCredits()

        lbslope = (avgCredits - 50) / lines

        try:
            with open(os.path.join("balanceLogs", str(userid)), 'r') as f:
                balanceLogs = f.readlines()                

            # Start from the end of the file
            for ln in balanceLogs:
                ## SCORE CALC ##
                cred = float(ln.split(" ")[1])
                unity = float(ln.split(" ")[2])

                # Add to total
                totalCred += cred
                totalUnity += unity
                logs += 1


                # Calculate score
                # Avg credits
                credScore = 2 * (totalCred / logs)
                if credScore > 5000: credScore = 5000

                # Avg unity 
                unityScore = 15 * (totalUnity / logs)

                # Log score
                transScore = ((logs / 2) ** 0.5) * 100
                if transScore > 5000: transScore = 5000
                
                # Calculate leaderboard score 
                avgLbCred = avgCredits * lbslope * logs + 50

                if cred > avgLbCred * 1.20:
                    lbScore = 7.5
                elif cred < avgLbCred * 0.85:
                    lbScore = 2.5
                else:
                    lbScore = 5
                lbScore *= 100

                # Score
                # It is credScore + unityScore + transactionsScore
                score = credScore + unityScore + transScore + lbScore

                ## END SCORE CALC ##

                balances.append(score)


        except FileNotFoundError:
            await message.send(embed=errorMsg("No balance logs have been recorded!"))
            return 
        
        balances.append(calcScore(User(userid)))

        # If there is only 1 item in the list, nothing will be graphed, so add the same value to the balance.
        xvalues = [i for i in range(len(balances))]

        # If too much data then don't show on graph
        if len(xstrs) < 30:
            plt.xticks(xvalues, xstrs)
        else:
            tf = "Indexes"

        # Create plot
        plt.xlabel(f"Index")
        plt.ylabel("Score")
        plt.title(f"{user.display_name}'s approximate score changes")

        # Slope color
        try:
            first, last = balances[0], balances[-1]
            if first > last: color = 'red'
            elif first < last: color = 'green'
            else: color = 'gray'
        except IndexError:
            color = 'gray'

        plt.plot(xvalues, balances, color=color)

        plt.savefig(f"temp/bal{userid}.png")
        plt.clf()

        file = discord.File(f"temp/bal{userid}.png", filename=f"balanceGraph.png")
        embed = discord.Embed(title="Score Graph", color=0xFF00FF)
        embed.set_footer(text="Score graph is approximate and may differ significantly or slightly from the actual scores.")
        embed.set_image(url=f"attachment://balanceGraph.png")

        await message.send(file=file, embed=embed)

        os.remove(f"temp/bal{userid}.png")
