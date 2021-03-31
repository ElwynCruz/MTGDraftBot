

# MTGDraftBot
This is a Discord bot created using Python to simulate a Magic: The Gathering draft among multiple players. At the moment, it supports a cube draft using the Cruzian Cube found [here](https://cubecobra.com/cube/list/cruzian)

## Getting Started ## 
1. Pull the repository. 
2. If necessary, update card_base.json to reflect all MTG cards (in case of new  set releases) and update CruzianPowerCube.csv to be a .csv file exported from [CubeCobra](https://cubecobra.com/). 
3. To generate your card base, run data/createDraftPool.py and it should generate a .json file for your card base.
4. Create a discord bot, and get it's token.
5. Add a .env file containing the token of the discord bot to the root directory. 
6. Finally, run the bot using src/MTGDraftBot.py and it will start the bot using the discord token to login.
7. Use commands as necessary to moderate the draft.
8. 
## Commands ##

### !draft ###
Creates a draft for players to join. To join it, use !join and to start it, use !start. This should be used in the public channel.

### !join ###
Joins a draft that has been created. This also opens up a DM channel for you to communicate with the bot and send future commands. This should be used in the public channel.

### !start ###
Starts the draft. This DMs all players who have joined a pack of cards. This should be used in the public channel. 

### !picks <timeout> ###
Shows you all the cards you have picked. This should only be used in your private DM with the bot.

### !quit ### 
This ends the draft prematurely. This should only be used in the public channel. 
