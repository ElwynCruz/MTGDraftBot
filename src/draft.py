import random
import json
from player import Player
from card import Card
class Draft:
  def __init__(self, packSize=15):
    self.started = False
    self.players = []
    self.pickedPlayers = []
    self.cardPoolPath = "../data/CruzianCards.json"
    self.packSize = packSize
  def addPlayer(self, player):
    self.players.append(player)
  def addPlayerToPicked(self, player):
    self.pickedPlayers.append(player)
  def getPlayerByName(self, name):
    for player in self.players:
      if player.name == name:
        return player
    return None
  def passPacks(self):
    placeholder = self.players[-1].picks
    for player in self.players:
      player.picks, placeholder = placeholder, player.picks
  def generatePicks(self):
    with open(self.cardPoolPath) as cardPool:
      allCards = json.load(cardPool)
      # generate a unique combination of cards for each player
      picksToGenerate = self.packSize * len(self.players)
      randomPicks = random.sample(range(len(allCards)), picksToGenerate)
      for index, player in enumerate(self.players):
        curIndex = index*self.packSize
        pack = randomPicks[curIndex:curIndex+self.packSize]
        hand = {}
        for card in pack:
          # create the card object, and store it in a list of cards 
          try:
            currentCard = Card(allCards[card]["name"], allCards[card]["img_uri"])
            hand[currentCard.name] = currentCard
          except:
            # if we have no image_uri for the card, just use its name as a placeholder
            currentCard = Card(allCards[card]["name"], allCards[card]["name"])
            hand[currentCard.name] = currentCard
        player.currentHand = hand
  def start(self):
    self.started = True
    self.generatePicks()
  