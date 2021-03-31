import random
import json
import os
import asyncio
from enum import Enum
from pathlib import Path
from player import Player
from card import Card

class Status(Enum):
  CREATED = 0 # created and accepting players
  WAITING = 1 # waiting on input from players
  TIMEOUT = 2 # pick timed out
  UPDATED = 3 # change made in draft that needs to be sent
  FINISHED = 4 # all picks are done
  TERMINATED = 5 # terminated early

class Draft:
  # TODO : add support for user uploaded card bases
  # TODO : add support for user defined draft packs/sizes/timer
  def __init__(self, id, packSize=15, numPacks=3, cardPoolPath="data/CruzianCards.json", timer=120):
    self.id = id
    self.status = Status.CREATED
    self.players = []
    self.pickedPlayers = []
    parentDir = Path(__file__).parent.parent
    self.cardPoolPath = parentDir / cardPoolPath
    self.packSize = packSize
    self.numPacks = numPacks
    self.timer = timer
    self.picksLeft = 0
    self.packsLeft = numPacks
    self.timeLeft = timer
    self.quit = False
  def addPlayer(self, player):
    self.players.append(player)
  def pickForEachPlayer(self):
    for player in self.players:
      player.pick(player.selection)
      player.selection = ""
  def getPlayerByName(self, name):
    for player in self.players:
      if player.name == name:
        return player
    return None
  def passPacks(self):
    playerOrder = self.players
    
    placeholder = playerOrder[-1].currentHand
    for player in self.players:
      player.currentHand, placeholder = placeholder, player.currentHand
      player.handUpdated = True
    self.pickedPlayers = []
    self.picksLeft -= 1
    self.status = Status.UPDATED
    self.timeLeft = self.timer
    
  def nextPack(self):
    self.packsLeft -= 1
    self.picksLeft = self.packSize
    for player in self.players:
      player.openNewPack(self.packsLeft)
    self.status = Status.UPDATED
    self.timeLeft = self.timer
  def timeout(self):
    for player in self.players:
      if player not in self.pickedPlayers:
        firstCard = list(player.currentHand.keys())[0]
        player.select(firstCard)
    self.status = Status.TIMEOUT
    self.timeLeft = self.timer
  def makePacks(self):
    with self.cardPoolPath.open() as cardPool:
      allCards = json.load(cardPool)
      # generate a unique combination of cards for each player
      cardsPerPlayer = self.packSize * self.numPacks
      picksToGenerate = cardsPerPlayer * len(self.players)
      randomPicks = random.sample(range(len(allCards)), picksToGenerate)
      for index, player in enumerate(self.players):
        curIndex = index*cardsPerPlayer
        packs = []
        for packNum in range(self.numPacks):
          offset = packNum * self.packSize
          cards = randomPicks[curIndex+offset:curIndex+self.packSize+offset]
          pack = {}
          for card in cards:
            # create the card object, and store it in a list of cards 
            try:
              currentCard = Card(allCards[card]["name"], allCards[card]["img_uri"])
              pack[currentCard.name] = currentCard
            except:
              # if we have no image_uri for the card, just use its name as a placeholder
              currentCard = Card(allCards[card]["name"], allCards[card]["name"])
              pack[currentCard.name] = currentCard
          packs.append(pack)
        player.packs = packs

  def isPackFinished(self):
    return self.picksLeft == 0

  def isDraftFinished(self):
    return self.packsLeft == 0 and self.isPackFinished()

  def hasEveryonePicked(self):
    return len(self.players) == len(self.pickedPlayers)

  def hasPickTimedOut(self):
    return self.timeLeft <= 0

  def hasQuit(self): 
    return self.quit
  def quit(self):
    self.quit = True

  # return whether the draft has been changed
  # this runs one iteration of the draft and should be continuously called until the draft is finished
  def updateDraft(self):
    if self.hasQuit():
      self.status = Status.TERMINATED
      return self.status
    self.status = Status.WAITING
    for player in self.players:
      if player.hasSelected() and player not in self.pickedPlayers:
        self.pickedPlayers.append(player)
    if self.isDraftFinished() and self.isPackFinished():
      self.status = Status.FINISHED
    elif self.isPackFinished():
      self.nextPack()
      self.players.reverse()
    elif self.hasEveryonePicked():
      self.pickForEachPlayer()
      self.passPacks()
    elif self.hasPickTimedOut():
      self.timeout()
    
    self.timeLeft -= 1
    return self.status

  # setup the draft so we are ready to run it
  def setup(self):
    self.status = Status.WAITING
    self.makePacks()