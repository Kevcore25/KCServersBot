# KCServers Bot
A private Discord bot for the KCMC Discord servers.
Intended to provide utilities for KCMC servers, as well as providing a fun, gambling-based virtual economy system.

It requires a JSON file called botsettings.json in order to run, as well as a .env file with a DISCORD_TOKEN variable.

Template for botsettings.json:
```json
{
    "admins": [],
    "prefix": "",
    "inflation amount": 1000,
    "KMCExtract": "",
    "AI Channel": 0,
    "Server ID": 0,

    "KCash Rate": 0.01,
    "Exchange fee": [500, 5],
    "Debug": false
}```