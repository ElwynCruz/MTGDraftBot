class Player:
  def __init__(self, name, discordUser):
    self.name = name
    self.picks = []
    self.currentHand = {}
    self.packs = []
    self.discordUser = discordUser
    self.selection = ""
  def select(self, cardName):
    self.selection = cardName
  def hasSelected(self):
    return self.selection in self.currentHand
  def pick(self, cardName):
    pickedCard = self.currentHand.pop(cardName)
    self.picks.append(pickedCard)
  def autopick(self):
    firstCard = list(self.currentHand.keys())[0]
    self.pick(firstCard)
    return firstCard
  def openNewPack(self, packNum):
    self.currentHand = self.packs[packNum]

