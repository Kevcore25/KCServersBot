import json, time, threading

userTemplate = {
    "credits": 0,
    "unity": 50,
    "gems": 0,
    "tags": [],
    "items": {},
    "IGN": None,
    "LFN": None,
    "job": None,
    "dailyTime": 0,
    "hourlyTime": 0,
    "incomeCmdsUsed": 0
}

botID = 0

def check_items(user) -> bool:
    """Checks for expired items and deletes them"""
    items: list = user.getData('items')

    deletedAnItem = False

    for i in items.copy():
        if int(time.time()) - i['expires'] > 0 and i['expires'] != -1:
            items.remove(i)
            deletedAnItem = True

    return user.setValue("items", items) if deletedAnItem else False

class User:
    def __init__(self, ID, doNotCheck = False):
        if str(botID) == str(ID):
            self.ID = "main"
        else:
            self.ID = str(ID)
        
        try:
            with open(f"users/{self.ID}.json", "r") as f:
                self.data = json.load(f)

            # Check for expired items in a thread. If an error occurs then the rest of the code should continue
            if not doNotCheck: threading.Thread(target=check_items, args=[self], daemon=True).start()

        except FileNotFoundError:
            self.createAccount()

    def delete_item(self, item: str, all: bool = False) -> bool:
        """
        Deletes an item. If all is specified, then all items of that item ID will be deleted
        If the item cannot be deleted (not found) then False will be returned
        """

        items: list = self.getData('items')

        deletedAnItem = False
        for i in items.copy():
            if item == i['item']:
                del items[i]
                deletedAnItem = True
                if not all: break

        return self.setValue("items", items) if deletedAnItem else False
    
    def add_item(self, item: str, expiry: int = -1) -> bool:
        """Adds an item"""
        items: list = self.getData('items')

        items.append({
            "item": item, 
            "expires": int(time.time() + expiry) if item['expires'] != -1 else -1,
            "data": {}
        })

        # Add item
        return self.setValue("items", items)


    def saveAccount(self, data = None):
        """Saves the user account"""
        if data is None:
            data = self.data

        with open(f"users/{self.ID}.json", "w") as f:
            json.dump(data, f)

    def createAccount(self):
        """Creates a user account"""

        self.data = userTemplate
        self.saveAccount()

    def getData(self, key = None) -> dict:
        if key is None:
            return self.data
        else:
            return self.data[key]
        

    def setValue(self, key: str, value) -> bool:
        self.data[key] = value
        self.saveAccount()
        return True
    
    def changeMainBal(self, credits) -> bool:
        """Changes the balance of main."""
        return User("main").addBalance(-credits)

    def addBalance(self, credits=0, unity=0, gems=0) -> bool:
        
        # negUnityFee = 1
        # if self.data["unity"] < 0:
        #     negUnityFee + self.data["unity"]

        self.data["credits"] = round(self.data["credits"] + credits, 5)

        if self.ID != "main": self.changeMainBal(credits)

        self.data["unity"] = round(self.data["unity"] + unity, 5)

        self.data["gems"] = round(self.data["gems"] + gems, 5)

        if self.data["unity"] > 200:
            self.data["unity"] = 200
        elif self.data["unity"] < -100:
            self.data["unity"] = -100

        self.saveAccount()        


        timeStr = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

        try:
            with open("balanceLog.txt", "a") as f:
                f.write(f"[{timeStr}] {self.ID}: {'+'+str(credits) if credits > 0 else credits} CRED, {'+'+str(unity) if unity > 0 else unity} UNITY (Now {self.data['credits']} CRED, {self.data['unity']} UNITY)\n")
        except FileNotFoundError:   
            print("BalanceLog file not found, creating new one")
            with open("balanceLog.txt", "w") as f:
                f.write(f"[{timeStr}] {self.ID}: {'+'+str(credits) if credits > 0 else credits} CRED, {'+'+str(unity) if unity > 0 else unity} UNITY (Now {self.data['credits']} CRED, {self.data['unity']} UNITY)\n")

        return True
       

    def delete_item(self, item: str, all: bool = False) -> bool:
        """
        Deletes an item. If all is specified, then all items of that item ID will be deleted
        If the item cannot be deleted (not found) then False will be returned
        """

        items: list = self.getData('items')

        deletedAnItem = False
        for i in items.copy():
            if item == i['item']:
                del items[i]
                deletedAnItem = True
                if not all: break

        return self.setValue("items", items) if deletedAnItem else False