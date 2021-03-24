class Player:
  def __init__(self, name, discordUser):
    self.name = name
    self.picks = []
    self.currentHand = {}
    self.discordUser = discordUser
  def pick(self, cardName):
      pickedCard = self.currentHand.pop(cardName, None)
      self.picks.append(pickedCard)

