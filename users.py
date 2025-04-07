import json, time, threading, os

userTemplate = {
    "credits": 0,
    "unity": 50,
    "gems": 0,
    "tags": [],
    "items": {},
    "job": None,
    "dailyTime": 0,
    "hourlyTime": 0,
    "bs%": 0,
    "rob": {
        "atk": 5,
        "def": 5, 
        "insights": 0,
        "won/lost": [0, 0],
        "attackedTime": 0,
        "attackTime": 0,
    },
    "log": 0,
    "redeemedCodes": [],
    "settings": {}
}

botID = 0

def check_items(user) -> bool:
    """Checks for expired items and deletes them"""
    items: dict = user.getData('items')

    deletedAnItem = False

    for id, item in items.copy().items():
        for expiry in item['expires']:
            if int(time.time()) - expiry > 0 and expiry != -1:                
                deletedAnItem = True

                items[id]['count'] -= 1
                if items[id]['count'] <= 0:
                    del items[id]
                    break
                items[id]['expires'].remove(expiry)

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

    def update(self) -> bool:
        """
        Updates the account to find missing keys from the template.
        This is a "soft" update, where only missing keys will be found.
        Returns True if updated, else False
        """

        data = self.getData()
        updated = False
        for key in userTemplate:
            if key not in data:
                updated = True
                data[key] = userTemplate[key]
        
        if updated:
            self.saveAccount(data)

        return updated

    def delete_item(self, item: str, count: int = 1, all: bool = False) -> bool:
        """
        Deletes an item. If all is specified, then all items of that item ID will be deleted
        If the item cannot be deleted (not found) then False will be returned
        """

        items: dict = self.getData('items')

        try:
            if all:
                del items[item]
            else:
                items[item]['count'] -= count                
                items[item]['expires'].pop(0)        
                if items[item]['count'] <= 0:
                    del items[item]
            deletedAnItem = True
        except KeyError as e:
            print(f"Warning: Unable to delete item {item} for {self.ID}: {e}")
            deletedAnItem = False

        if deletedAnItem:
            return self.setValue("items", items)
        else:
            return False
        
    def get_item(self, item: str, onlydetermine: bool = True) -> None | dict:
        """
        Gets an item. If the item does not exist, then None will be returned
        """

        items: dict = self.getData('items')

        # Check if the item exists
        if item in items:
            # Get item data
            return items[item] if not onlydetermine else True
        else:
            return None if not onlydetermine else False


    def add_item(self, item: str, expiry: int = -1, count: int = 1, data: dict = {}) -> bool:
        """Adds an item"""
        items: dict = self.getData('items')

        exp = int(time.time() + expiry) if item['expires'] != -1 else -1,

        if item in items:
            items[item] = {
                "expires": [exp],
                "data": data,
                "count": count
            }
        else:
            items[item]['count'] += count
            items[item]['expiry'].append(exp)

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

    def getData(self, key = None):
        if key is None:
            return self.data
        else:
            if key not in self.data:
                # Attempt to "soft" update
                self.update()
            return self.data[key]
        

    def setValue(self, key: str, value) -> bool:
        self.data[key] = value
        self.saveAccount()
        return True
    
    def changeMainBal(self, credits) -> bool:
        """Changes the balance of main."""
        return User("main").addBalance(-credits)

    def log(self, msg: str = "", user: str = None) -> str:
        # Override user
        if user is None:
            user = str(self.ID)
        
        timeStr = int(time.time())

        # The log list is shortened to: 
        # {time} {credits} {unity} {gems} {msg}
        data = self.getData()
        log = f"{timeStr} {data['credits']} {data['unity']} {data['gems']} {msg}"

        # Add to user logs

        try:
            if user not in os.listdir('balanceLogs'):
                with open(os.path.join("balanceLogs", user), 'w') as f:
                    f.write(log)
            else:
                # Append to the log file
                with open(os.path.join("balanceLogs", user), "a") as f:
                    f.write("\n" + log)
        except (FileNotFoundError):
            # Create a folder if it does not exist
            if "balanceLogs" not in os.listdir():
                os.mkdir("balanceLogs")

            # Create a new file
            with open(os.path.join("balanceLogs", user), 'w') as f:
                f.write(log)

        # Increase amount of log for user by 1
        try:
            self.setValue(
                "log", 
                self.getData("log") + 1
            )
        except KeyError:
            self.setValue(
                "log", 1
            )

        return log
    
    def addBalance(self, credits=0, unity=0, gems=0) -> bool:
        
        # negUnityFee = 1
        # if self.data["unity"] < 0:
        #     negUnityFee + self.data["unity"]

        self.data["credits"] = round(self.data["credits"] + credits, 5)

        if self.ID != "main": self.changeMainBal(credits)

        self.data["unity"] = round(self.data["unity"] + unity, 5)

        self.data["gems"] = round(self.data["gems"] + gems)

        if self.data["unity"] > 100:            
            self.data['credits'] += (self.data["unity"] - 100) # Convert excess Unity into Credits
            self.data["unity"] = 100
        elif self.data["unity"] < -100:
            self.data["unity"] = -100

        self.saveAccount()        

        # Log balances
        self.log()

        return True