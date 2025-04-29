
from csv import reader
import json, threading, requests

sheetsURL = "https://docs.google.com/spreadsheets/d/19nHv9ElrIgJgL23WzKzQ94nZGc172dOyWaEOLU16amc/export?format=csv"
def parseDFV(value):
    try:
        return float(value)
    except ValueError:
        return str(value)

def updateTimer():
    threading.Timer(300, updateTimer).start()
    update()

def update():
    print("Refreshing Question Bank data")
    data = requests.get(sheetsURL, timeout=3).content

    with open("questionBank.csv", "wb") as f:
        f.write(data)

    with open("questionBank.csv", 'r', encoding='utf-8') as f:
        data = list(reader(f))

    preload(data)
    print("Refreshed Question Bank data")

def preload(data):
    """Converts the .csv file into a readable JSON file"""
    # PRELOAD
    questions = {}
   # for values in df.values[2:]:
    for i, values in enumerate(data[1:]):
        try:
            #Example
            # ['End portal frames when activated output a redstone signal of?', 'Minecraft / KCMC', 'They cannot have a signal; this is a trick question!', '14', '16', '15', '0', 'C', '0.05', '20.00', '0', '60', '20', '0.05', '', '']
            
            question = str(values[0]).replace("\\n", "\n")

            # Skip
            if question.lower().startswith("[ignore]"):
                continue
            
            subject = parseDFV(values[1])

            optionsTemp = list(values[2:7])
            options = []

            for o in optionsTemp:
                if "nan" in str(o): break

                options.append(str(o))
            

            answer = str(values[7])
            grade = str(values[10])
            
            if "nan" in str(values[11]).lower():
                timelimit = 20
            else: 
                timelimit = int(values[11])

            # def defaults(value, default, index):
            #     if "nan" in str(value).lower():
            #         return default
            #     else:
            #         return float(values[index]) 
                
            defaults = lambda default, index: default if "nan" in str(values[index]).lower() else float(values[index])

            unityGain = defaults(0.1, 8)
            creditGain = defaults(20, 9)
            
            unityLost = defaults(0.5, 13)
            creditLost = defaults(30, 12)
        
            if len(values) >= 14 and "nan" not in str(values[14]).lower():
                hint = str(values[14])
            else:
                hint = None

            # +2 to match sheets
            questions[i + 2] = {
                "question": question,
                "subject": subject,
                "options": options,
                "answer": answer,
                "unityGain": unityGain,
                "creditGain": creditGain,
                "grade": grade,
                "timelimit": timelimit,
                "creditLost": creditLost,
                "unityLost": unityLost,
                "hint": hint
            }
        except ValueError: pass
        except Exception as e:
            print(f"Cannot do {', '.join(str(i) for i in values)}: {e}")

        # print(f"{round( (i+1) / valuesLen * 100 )}% Done", end='\r')

    # Remove incorrects

    for i in questions.copy():
        if "nan" in str(questions[i]):
            del questions[i]


    with open("questionData.json", "w") as f:
        json.dump(questions, f, indent=4)
    with open("questionData.json", "r") as f:
        data = f.read()
        data = data.replace("NaN", "null")
    with open("questionData.json", "w") as f:
        f.write(data)






def sortBySubject():
    """Adds a dictionary that contains SUBJECT: [indexes], ..."""

    subjects = {}

    for index in questions:
        subject = questions[index]["subject"].upper()
        if subject in subjects:
            subjects[subject].append(index)
        else:
            subjects[subject] = [index]

    return subjects




# def generate_index(
#     subject = "ALL"
# )

# def parse(index: int):
#     """Parses the data given an index"""
    
        
if "__main__" in __name__:
    update()


with open("questionData.json", "r") as f:
    questions = json.load(f) 
