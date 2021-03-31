import discord
import io
import os
import asyncio
from dotenv import load_dotenv
from discord.ext import commands, tasks
from draft import Draft, Status
from player import Player

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents(messages=True, guilds=True)
intents.reactions = True
description = "A bot that runs a Magic: The Gathering  Draft. Currently supports only the Cruzian Cube."
help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)

bot = commands.Bot(command_prefix='!',
                  intents=intents,
                  description=description,
                  help_command=help_command,
                  )

drafts = {} # guild.id : draft
messagesToDelete = {} # draft : message
statusMessages = {} # draft : message

@bot.event
async def on_ready():
  print('We have logged in')
  print(bot.user.id)

@bot.event
async def on_disconnect():
  print("disconnecting")

def getPickOrder(draft):
  playerNames = [player.name for player in draft.players]
  pickOrderMsg = "\n".join(playerNames)
  return pickOrderMsg

def getDraftState(draft):
  embedResponse = discord.Embed(title="DRAFT INFORMATION")

  packNum = draft.numPacks - draft.packsLeft
  pickNum = draft.packSize - draft.picksLeft + 1
  embedResponse.set_author(
    name=bot.user.name,
    icon_url=bot.user.avatar_url
  )

  embedResponse.add_field(
    name="SETTINGS",
    value="""Players: {}\nPack Size: {}\nNumber Packs: {}\nTimer: {}\n"""
            .format(len(draft.players), draft.packSize, draft.numPacks, draft.timer),
    inline=True
  )

  embedResponse.add_field(
    name="STATUS",
    value="Pack #{}\n Pick #{}\n Time Left:{}".format(packNum, pickNum, draft.timeLeft),
    inline=True
  )
  
  embedResponse.add_field(
    name="PICK ROTATION (top to bottom)",
    value = getPickOrder(draft),
    inline=False
  )

  unpickedPlayers = [player.name for player in draft.players if player not in draft.pickedPlayers]
  embedResponse.add_field(
    name="WAITING ON",
    value = ", ".join(unpickedPlayers),
    inline=False
  )

  return embedResponse

async def select(player, cardName):
  response = "You are selecting **{}**".format(cardName)
  player.select(cardName)
  await player.discordUser.send(response, delete_after=10)

async def autoselect(player):
  cardName = player.selection
  response = "Your pick is timing out. You are automatically selecting **{}**".format(cardName)
  await player.discordUser.send(response, delete_after=10)

#################################################
##########          EVENTS             ##########
#################################################

# handle pick reactions
@bot.event
async def on_raw_reaction_add(payload):
  message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
  user = await bot.fetch_user(payload.user_id)
  if (message.author.id == bot.user.id and
      isinstance(message.channel, discord.DMChannel) and
      len(message.embeds) > 0):
    cardName = message.embeds[0].title
    username = user.name
    for draft in drafts.values():
      player = draft.getPlayerByName(username)
      if player is not None:
        await select(player, cardName)
        break

@bot.event
async def on_command_error(ctx, error):
  # if command has local error handler, return
  if hasattr(ctx.command, 'on_error'):
    return

  # get the original exception
  error = getattr(error, 'original', error)

  if isinstance(error, commands.CommandNotFound):
    return

  if isinstance(error, commands.BotMissingPermissions):
    missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
    if len(missing) > 2:
        fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
    else:
        fmt = ' and '.join(missing)
    _message = 'I need the **{}** permission(s) to run this command.'.format(fmt)
    await ctx.send(_message)
    return

  if isinstance(error, commands.MissingPermissions):
    missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
    if len(missing) > 2:
        fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
    else:
        fmt = ' and '.join(missing)
    _message = 'You need the **{}** permission(s) to use this command.'.format(fmt)
    await ctx.send(_message)
    return

  if isinstance(error, commands.UserInputError):
    await ctx.send("Invalid input.")
    return

  if isinstance(error, commands.NoPrivateMessage):
    try:
        await ctx.author.send('This command cannot be used in direct messages.')
    except discord.Forbidden:
        pass
    return
  if isinstance(error, commands.PrivateMessageOnly):
    try:
        await ctx.send('This command can only be used in direct messages.')
    except discord.Forbidden:
        pass
    return

  if isinstance(error, commands.CheckFailure):
    await ctx.send("You do not have permission to use this command.")
    return

#################################################
##########       HELPER FUNCTIONS      ##########
#################################################

async def showCardsToPlayer(player, cards):
  sends = []
  for card in cards:
    embed = discord.Embed(title=card.name)
    if isinstance(card.img_uri,  list):
      front = card.img_uri[0]
      back = card.img_uri[1]
      embed.set_image(url=front)
      embed.set_thumbnail(url=back)
    else:
      embed.set_image(url=card.img_uri)
    sends.append(player.discordUser.send(embed=embed))
  return await asyncio.gather(*sends)

async def showPicks(player, cards, timeout):
  sends = []
  for card in cards:
    embed = discord.Embed(title=card.name)
    if isinstance(card.img_uri,  list):
      front = card.img_uri[0]
      back = card.img_uri[1]
      embed.set_image(url=front)
      embed.set_thumbnail(url=back)
    else:
      embed.set_image(url=card.img_uri)
    sends.append(player.discordUser.send(embed=embed, delete_after=timeout))
  await asyncio.wait(sends)

async def sendUpdates(draft):
  updates = [showCardsToPlayer(player, player.currentHand.values()) for player in draft.players]
  cardMsgs = await asyncio.gather(*updates)
  msgs = [msg for sublist in cardMsgs for msg in sublist] 
  messagesToDelete[draft] = [*messagesToDelete[draft], *msgs] 

async def sendTimeouts(draft):
  updates = [autoselect(player) for player in draft.players if player not in draft.pickedPlayers]
  await asyncio.wait(updates)

async def deletePackMsgs(draft):
  msgs = messagesToDelete[draft]
  if msgs:
    msgDeletes = [msg.delete() for msg in msgs]
    await asyncio.wait(msgDeletes)
    messagesToDelete[draft] = []

async def writeDecklist(player):
  with io.BytesIO() as buf:
    for pick in player.picks:
      name = "{}\n".format(pick.name)
      buf.write(name.encode('utf-8'))
    buf.seek(0)
    filename = "{}_decklist.txt".format(player.name)
    file = discord.File(buf, filename=filename)
    await player.discordUser.send("Here is your decklist:", file=file)

async def endDraft(draft):
  sendDecklists = [writeDecklist(player) for player in draft.players]
  sendEndMsg = [player.discordUser.send("The draft has ended. Generating your decklist now...") for player in draft.players]
  await asyncio.wait(sendEndMsg)
  await asyncio.wait(sendDecklists)


async def deleteDMs(draft):
  deletes = []
  for player in draft.players:
    async for message in player.discordUser.dm_channel.history(limit=100):
      if message.author == bot.user:
        deletes.append(message.delete())
  await asyncio.wait(deletes)

@tasks.loop(seconds=1)
async def runDrafts():
  
  if not drafts:
    runDrafts.stop()
  else: 
    updatedDrafts = []
    doneDraftIDs = []
    updatedStatuses = []
    deletes = []

    for id, draft in drafts.items():
      draftStatus = draft.updateDraft()
      if draftStatus == Status.TIMEOUT:
        await deletePackMsgs(draft)
        updatedDrafts.append(sendTimeouts(draft))
      elif draftStatus == Status.UPDATED:
        await deletePackMsgs(draft)
        updatedDrafts.append(sendUpdates(draft))
      elif draftStatus == Status.FINISHED:
        doneDraftIDs.append(id)
        channel = bot.get_channel(draft.id)
        deletes.append(channel.delete())
        deletes.append(endDraft(draft))
        deletes.append(deleteDMs(draft))
      elif draftStatus == Status.TERMINATED:
        doneDraftIDs.append(id)
        channel = bot.get_channel(draft.id)
        deletes.append(channel.delete())
        deletes.append(deleteDMs(draft))
      elif draftStatus == Status.WAITING:
        updatedStatus = getDraftState(draft)
        updatedStatuses.append(statusMessages[draft].edit(content=None, embed=updatedStatus))
      
    if updatedStatuses:
      await asyncio.wait(updatedStatuses)
    if updatedDrafts:
      await asyncio.wait(updatedDrafts)
    if deletes:
      await asyncio.wait(deletes)
    for draftID in doneDraftIDs:
      drafts.pop(draftID)




#################################################
##########          CHECKS            ##########
#################################################

async def doesDraftExist(ctx):
  return ctx.guild.id in drafts

def doesDraftStatusEqual(status):
  async def predicate(ctx):
    return drafts[ctx.guild.id].status == status
  return commands.check(predicate)

async def isDraftChannel(ctx):
  draft = drafts[ctx.guild.id]
  return draft.id == ctx.channel.id

async def isUniquePlayer(ctx):
  draft = drafts[ctx.guild.id]
  for player in draft.players:
    if player.name == ctx.author.name:
      return False
  return True

#################################################
##########           COMMANDS         ##########
#################################################

@bot.command(name='draft')
@commands.guild_only()
async def draft(ctx):
  """
  Creates a new draft. 
  Only one draft can be active in a server
  Creates a new text channel for the draft.
  """
  if ctx.guild.id not in drafts:
    channel = await ctx.guild.create_text_channel('DRAFT-CHANNEL')
    draft = Draft(channel.id)
    drafts[ctx.guild.id] = draft
    messagesToDelete[draft] = []
    response = ctx.author.mention + ' has started a draft!\n'
    response += 'Please use {} for future commands and updates.'.format(channel.mention)
    rulesEmbed = discord.Embed(
      title="MTGDraftBot Guide", 
      description="MTGDraftBot uses discord messages and commands to simulate a live MTG Draft."
    )
    rulesEmbed.set_author(name="Elwyn Cruz")
    rulesEmbed.add_field(
      name="Getting Started",
      value="""After creating a draft, users can !join to put themselves in the draft.
               Once everyone has joined, use !start to begin. You can check the status
               of the draft (pick order, time left, who has not picked) in this channel.""",
      inline=False
    )
    rulesEmbed.add_field(
      name="Drafting",
      value="""Once you start the draft, MTGDraftBot will DM each player individually.
               After you get all of your picks, you can react to any of them to select it.
               You will have until the timer runs out or until everyone has selected a card
               to change your pick.""",
      inline=False
    )
    rulesEmbed.add_field(
      name="Useful Commands",
      value="""!join : join the draft. Use this in this channel.
               !start : start the draft. Use this in this channel.
               !players : list the players in the draft. Use this in this channel.
               !picks <timeout> : see your picks. They will expire after <timeout> 
               seconds to ensure that it doesn't clutter up the draft. Use this in 
               your DM Channel with MTGDraftBot.
                """,
      inline=False
    )
    await ctx.send(response, delete_after=30)
    await channel.send(embed=rulesEmbed)
  else:
    ctx.send("There is already a draft going on!", delete_after=30)


@bot.command(name='join')
@commands.guild_only()
@commands.check(doesDraftExist)
@commands.check(isDraftChannel)
@commands.check(isUniquePlayer)
@doesDraftStatusEqual(Status.CREATED)
async def join(ctx):
  """
  Joins a draft that has already been created.
  """
  newPlayer = Player(ctx.author.name, ctx.author)
  draft = drafts[ctx.guild.id]
  draft.addPlayer(newPlayer)
  response = ctx.author.mention + ' has joined the draft!\n'
  response += 'There are ' + str(len(drafts[ctx.guild.id].players)) + ' people participating in this draft.'
  dm_response = 'Welcome to the draft! Please check the channel for updates.'
  await ctx.send(response)
  await newPlayer.discordUser.send(dm_response, delete_after=60)

@bot.command(name='start')
@commands.guild_only()
@commands.check(doesDraftExist)
@commands.check(isDraftChannel)
@doesDraftStatusEqual(Status.CREATED)
async def start(ctx):
  """
  Starts a draft with all the players that have joined it.
  This begins sending packs to each player for them to pick.
  """
  draft = drafts[ctx.guild.id]
  statusString = "Starting the draft with {} players".format(str(len(draft.players)))
  statusMessages[draft] = await ctx.send(statusString)
  draft.setup()
  if (not runDrafts.is_running()):
    runDrafts.start()

@bot.command(name='players')
@commands.guild_only()
@commands.check(doesDraftExist)
@commands.check(isDraftChannel)
async def getPlayers(ctx):
  """
  Shows the members participating in the  draft.
  """
  draft = drafts[ctx.guild.id]
  names = [player.names for player in draft.players]
  response = ", ".join(names)
  response += " are participating in the draft."
  await ctx.send(response)


@bot.command(name='picks')
@commands.dm_only()
async def picks(ctx, timeout):
  """
  Shows the player their picks.
  The picks will disappear after <timeout> seconds.
  """
  for draft in drafts.values():
    player = draft.getPlayerByName(ctx.author.name) 
    if player is not None:
      picks = player.picks
      await showPicks(player, picks, int(timeout))
      break

@bot.command(name='quit')
@commands.guild_only()
@commands.check(doesDraftExist)
@commands.check(isDraftChannel)
async def quit(ctx):
  """
  Ends the draft early. No decklists will be generated.
  """
  draft = drafts[ctx.guild.id]
  draft.quit()

bot.run(TOKEN)