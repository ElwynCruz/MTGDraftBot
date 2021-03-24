import discord
import os
from dotenv import load_dotenv
from discord.ext import commands, tasks
from draft import Draft
from player import Player
client = discord.Client()

load_dotenv()
TOKEN = os.getenv('TOKEN')

ERROR_NO_DRAFT = 'There is no draft currently running!\n Use !draft to start a new draft'
ERROR_NO_CARD_NAME = 'The card you picked could not be found.'
ERROR_NOT_IN_DRAFT = 'You are not participating in a draft!'
ERROR_PICKED_ALREADY = 'You have already picked a card this pack! Use !picks to view cards you have picked'
bot = commands.Bot(command_prefix='!')
bot.draft = None

def draftIsCreated():
  if (bot.draft is None):
    return False
  else:
    return True
def draftIsStarted():
  return bot.draft.started
@tasks.loop(seconds=1)
async def passPacks():
  if len(bot.draft.pickedPlayers) == len(bot.draft.players):
    bot.draft.passPacks()


@bot.event
async def on_ready():
  print('We have logged in')

@bot.event
async def on_command_error(self, ctx, error):
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

  if isinstance(error, commands.DisabledCommand):
    await ctx.send('This command has been disabled.')
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
    await self.send_command_help(ctx)
    return

  if isinstance(error, commands.NoPrivateMessage):
    try:
        await ctx.author.send('This command cannot be used in direct messages.')
    except discord.Forbidden:
        pass
    return
  if isinstance(error, commands.PrivateMessageOnly):
    try:
        await ctx.author.send('This command can only be used in direct messages.')
    except discord.Forbidden:
        pass
    return

  if isinstance(error, commands.CheckFailure):
    await ctx.send("You do not have permission to use this command.")
    return

@bot.command(name='draft')
async def draft(ctx):
  bot.draft = Draft()
  response = ctx.author.name + ' has started a draft!\n'
  response += 'Type !join to join the draft'
  await ctx.send(response)

@bot.command(name='join')
@commands.check(draftIsCreated)
async def join(ctx):
  newPlayer = Player(ctx.author.name, ctx.author)
  bot.draft.addPlayer(newPlayer)
  response = newPlayer.name + ' has joined the draft!\n'
  response += 'There are ' + str(len(bot.draft.players)) + ' people participating in this draft.'
  dm_response = 'Welcome to the draft! Please check the channel for updates.'
  await ctx.send(response)
  await newPlayer.discordUser.send(dm_response)

@bot.command(name='start')
@commands.check(draftIsCreated)
async def start(ctx):
  if (bot.draft is not None):
    await ctx.send('Starting the draft with ' + str(len(bot.draft.players)) + ' players')
    bot.draft.start()
    passPacks.start()
    for player in bot.draft.players:
      # send each player the cards in their hand
      for _, card in player.currentHand.items():
        await player.discordUser.send(card.img_uri)
  else:
    await ctx.send(ERROR_NO_DRAFT)

@bot.command(name='quit')
@commands.check(draftIsCreated)
async def quit(ctx):
  if (bot.draft is not None):
    bot.draft = None
    await ctx.send("Quitting the draft now!")
  else:
    await ctx.send(ERROR_NO_DRAFT)
  
@bot.command(name='pick')
@commands.check(commands.dm_only)
@commands.check(draftIsStarted)
async def pick(ctx, *args):
  try:
    player = bot.draft.getPlayerByName(ctx.author.name)
    cardName = " ".join(args)
    if player not in bot.draft.pickedPlayers:
      player.pick(cardName)
      bot.draft.addPlayerToPicked(player)
      await player.discordUser.send("You picked " + cardName + ". Use !picks to view your picks.")
    else: 
      await player.discordUser.send(ERROR_PICKED_ALREADY)
    
  except KeyError:
    await player.discordUser.send(ERROR_NO_CARD_NAME)

@bot.command(name='picks')
@commands.check(commands.dm_only)
@commands.check(draftIsStarted)
async def picks(ctx):
  try:
    player = bot.draft.getPlayerByName(ctx.author.name)
    picks = player.picks
    await player.discordUser.send(picks)
  except:
    await ctx.send(ERROR_NOT_IN_DRAFT)

bot.run(TOKEN)