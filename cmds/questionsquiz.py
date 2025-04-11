import discord
from discord.ext import commands
from calculatefuncs import *
import threading, asyncio, re
import questionparser

threading.Thread(target=questionparser.updateTimer).start()

class QuestionsQuiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(
        help = f"Question",
        description = "Gives a question that when answered correctly, grants you Credits and Unity, but when answered wrong, makes you lose Credits and Unity.\nSpecifiying a subject gives a -90% Credit Earnings for that question.",
        aliases = ['q', 'question']
    )
    @commands.cooldown(1, 3600, commands.BucketType.user) 
    async def questions(self, message: discord.Message, subject = "RANDOM"):


        u = User(message.author.id)

        if u.getData('job') != "Student":
            await message.send("Sorry, but until there are more questions in the bank, I am disabling this command lol good luck with your unity problems")
            self.questions.reset_cooldown(message)
            return
        subject = str(subject).upper()

        questionsSub = questionparser.sortBySubject()

        if subject == "RANDOM":
            subject = random.choice(list(questionsSub))

        def lost():
            """Loss function"""
            u.addBalance(-creditLoss, -unityLoss)
            
        if subject in questionsSub:

            index = random.choice(questionsSub[subject])

            question = questionparser.questions[index]


            letterNumConv = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}


            ## Grade scaling
            level = int(re.search(r'\d+', question['grade']).group())

            data = u.getData()

            if "grade" in data:
                grade = data['grade']
            else:
                grade = 10 # By default
            
            # Calc grade scaling
            # This should be the formula:
            # WIN REWARD: (Level - Grade) / 10 * 1.5 unless Level is 0 where win reward = +0%
            # LOSE REWARD: (Level - Grade) / 10 * 3 unless Level is 0 where lose reward = -0%
            if level > 0:
                gs_winRwd = round((level - grade) / 10 * 1.5 + 1, 1)
                gs_loseRwd = round((level - grade) / 10 * 3 + 1, 1)
            else:
                gs_winRwd, gs_loseRwd = 1, 1

            creditReward = round(calcCredit(question["creditGain"] * calcInflation() * gs_winRwd, u), 2)
            creditReward = round(creditReward / calcWealthPower(u, decimal=True), 2)

            if subject != "RANDOM": creditReward = round(creditReward / 10, 2)
            unityReward = round(question['unityGain'] / calcWealthPower(u, decimal=True), 2)

            creditLoss = round(question["creditLost"] * calcInflation() / gs_loseRwd, 2)
            unityLoss = round(question['unityLost'], 2)

            
            match subject:
                case "MATH": notice = "The use of GDCs (TI-83/84 Plus) and Desmos is allowed but not any generative source or the internet"
                case "SCIENCE" | "CHEMISTRY" | "PHYSICS": notice = "The use of calculators are allowed but not any generative source or the internet"
                case "ENGLISH": notice = "The use of a dictionary is allowed if specified in the question but not any generative source or the internet"
                case "SOCIAL": notice = "The use of any generative sources or the internet is not allowed"
                case _: notice = "The use of any generative sources or the internet is not allowed"

            ## BIG: If MULTIPLE CHOICE
            if question['options'][0].upper() != "WR":        

                options = {}
                multiplechoices = ["A", "B", "C", "D", "E"]

                # SHUFFLE MULTIPLE CHOICE

                questionOptions = question['options'].copy()            
                
                answer = question['options'][letterNumConv[question['answer']]-1]

                random.shuffle(questionOptions)


                for i in range(len(questionOptions)):
                    options[multiplechoices[i]] = questionOptions[i]

                optionsTxt = "\n".join(f"{choice}) {value}" for choice, value in options.items())
                temp = time.time()
                embed = discord.Embed(
                    title=f"{subject.capitalize()} Question (ID of {index})",
                    description=f"**Multiple Choice** - Level {question['grade']}```fix\n{question['question']}```\n{optionsTxt}\n\nRewards: `{creditReward} Credits`, `{unityReward} Unity`\nLosses: `{creditLoss} Credits`, `{unityLoss} Unity`\n*Expires <t:{int(temp) + question['timelimit']}:R>*",
                    color = 0xFF00FF,
                )
                embed.set_footer(text=notice)
                msg = await message.send(embed=embed)
                initTime = time.time()


                optionValues = {"🇦": "A", "🇧": "B", "🇨": "C", "🇩": "D", "🇪": "E"}
                # Add choices
                # await msg.add_reaction("🇦")
                # await msg.add_reaction("🇧")
                # await msg.add_reaction("🇨")
                # await msg.add_reaction("🇩")
                # await msg.add_reaction("🇪")

                for i in range(len(options)):
                    await msg.add_reaction(list(optionValues)[i])

                def check(reaction, user):
                    return user == message.author and (str(reaction.emoji) in list(optionValues))
                

                try:
                    userMsg = await self.bot.wait_for('reaction_add', timeout=int(temp - initTime + question['timelimit']), check=check)
                except asyncio.exceptions.TimeoutError:
                    await msg.edit(embed=errorMsg(f'You lost `{creditLoss} Credits` and `{unityLoss} Unity`!\nYou lost {round(100 / gs_loseRwd-100 , 1)}% less credits because of level scaling.', title="Time limit exceeded!"))
                    lost()
                    return
                
                userOption = optionValues[str(userMsg[0].emoji)]

                if questionOptions[letterNumConv[userOption]-1] == answer:    
                    await msg.clear_reactions()            
                    u.addBalance(creditReward, unityReward)
                    await msg.edit(embed=successMsg("Correct", f'You gained `{creditReward} Credits` and `{unityLoss} Unity`!\nYou gained {round(100 / gs_winRwd-100 , 1)}% more credits because of level scaling.\nIt took you `{round(time.time() - initTime, 2)} seconds` to answer the question.'))

                else:                
                    await msg.clear_reactions()
                    await msg.edit(embed=errorMsg(f'You lost `{creditLoss} Credits` and `{unityLoss} Unity`!\nYou lost {round(100 / gs_loseRwd -100 , 1)}% less credits because of level scaling.', title="Wrong!"))
    # userOption: {userOption}
    # question['options'][letterNumConv[userOption]-1]: {question['options'][letterNumConv[userOption]-1]}
    # answer: **{answer}** <- how is this wrong?!?!?!?!? lets do some debugging of JSUT THIS
    # ... answer = questionOptions[letterNumConv[question['answer']]-1]
    # ...... question['answer']: {question['answer']}
    # ...... questionOptions = {questionOptions}
    # ...... letterNumConv[question['answer']] = {letterNumConv[question['answer']]} 
    # question['options'] (ORIGINAL) = {question['options']}
    # options: {options}
    # """)
                    lost()
            else:
                # IF WRITTEN RESPONSE! NEW CODE
                answer = question['answer']
                temp = time.time()
                embed = discord.Embed(
                    title=f"{subject.capitalize()} Question (ID of {index})",
                    description=f"**Written Response / Short Answer** - Level {question['grade']}```fix\n{question['question']}```\n*Please send a message with your answer before the time limit expires!*\n\nRewards: `{creditReward} Credits`, `{unityReward} Unity`\nLosses: `{creditLoss} Credits`, `{unityLoss} Unity`\n*Expires <t:{int(temp) + question['timelimit']}:R>*",
                    color = 0xFF00FF,
                )
                embed.set_footer(text=notice)

                msg = await message.send(embed=embed)
                initTime = time.time()
                
                try:
                    userMsg = await self.bot.wait_for('message', check=lambda msg: msg.author == message.author, timeout=int(temp - initTime + question['timelimit']))
                except asyncio.exceptions.TimeoutError:
                    await msg.clear_reactions()
                    await msg.edit(embed=errorMsg(f'You lost `{creditLoss} Credits` and `{unityLoss} Unity`!\nYou lost {round(100 / gs_loseRwd -100, 1)}% less credits because of level scaling.', title="Time limit exceeded!"))
                    lost()
                    return
            
                if str(userMsg.content).lower().replace(" ","") == str(answer).lower().replace(" ", ""):                     
                    await msg.clear_reactions()
                    u.addBalance(creditReward, unityReward)
                    await msg.edit(embed=successMsg("Correct!",f'You gained `{creditReward} Credits` and `{unityLoss} Unity`!\nYou gained {round(100 / gs_winRwd - 100, 1)}% more credits because of level scaling.\nIt took you `{round(time.time() - initTime, 2)} seconds` to answer the question.'))
                else:                
                    await msg.clear_reactions()
                    await msg.edit(embed=errorMsg(f'You lost `{creditLoss} Credits` and `{unityLoss} Unity`!\nYou lost {round(100 / gs_loseRwd - 100 , 1)}% less credits because of level scaling.\n{(f"The correct answer starts with `{str(answer)[0]}...` (you answered {userMsg.content})") if len(str(answer)) > 1 else ""}', title="Wrong!"))
                    lost()
        else:
            await message.send(embed=errorMsg(f"{subject} is not a vaild subject!\nVaild subjects include: {', '.join(str(i).capitalize() for i in list(questionsSub))}\nNOTICE: Choosing a subject reduces rewards by 75%"))
            self.questions.reset_cooldown(message)

