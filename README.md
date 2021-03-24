# MTGDraftBot
This is a Discord bot created using Python to simulate a Magic: The Gathering draft among multiple players.

To start, pull the repository. To run, run src/MTGDraftBot.py and it will start the bot using the discord token to login. From there you can use the following commands:

!draft
Creates a draft for players to join. To join it, use !join and to start it, use !start. This should be used in the public channel.

!join
Joins a draft that has been created. This also opens up a DM channel for you to communicate with the bot and send future commands. This should be used in the public channel.

!start
Starts the draft. This DMs all players who have joined a pack of cards. This should be used in the public channel. 

!pick <card name>
Picks a card with name "card name" from your pack. If no such card exists, returns an error. Otherwise, it will remove the card from 
your pack and add it to your picks. Once everyone has picked, the packs will pass to the next player. Note that you must spell the name
correctly, including punctuation and all.
This should only be used in your private DM with the bot.

!picks
Shows you all the cards you have picked. This should only be used in your private DM with the bot.

!quit 
This ends the draft prematurely. This should only be used in the public channel. 
