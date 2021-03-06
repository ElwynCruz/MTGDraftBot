# INPUT_PATH : path to card base, which contains every card in magic the gathering from Scryfall and an output path
# CSV_FILE_PATH : .csv file that contains the name of every card we would like to have in the draft
# OUTPUT_PATH : .json file, which contains only card names and card images of cards found in the .csv file

import json
import csv
from pathlib import Path

CURRENT_DIRECTORY = Path(__file__).parent
INPUT_PATH = CURRENT_DIRECTORY / "card_base.json"
OUTPUT_PATH = CURRENT_DIRECTORY / "CruzianCards.json"
CSV_FILE_PATH = CURRENT_DIRECTORY / "CruzianPowerCube.csv"

def make_json(csvFilePath, jsonFilePath, outPath):
  cards = {}
  with open(INPUT_PATH, 'rb') as input_data, open(csvFilePath, 'r') as csvf, open(outPath, 'w') as output_file:
    json_data = json.load(input_data)
    csvReader = csv.DictReader(csvf)
    # first filter out the card base of all cards, saving only name and image
    for item in json_data:
      name = item['name']
      try:
        img_uri = item['image_uris']['normal']
        cards[name] = {
          "name": name,
          "img_uri": img_uri
        }
      except KeyError: # if image is not available, its probably a double faced card
        try:
          img_uris = []
          frontFace = item['card_faces'][0]
          frontName = frontFace['name']
          backName = item['card_faces'][1]['name']
          if frontName == backName: # Ranger-Captain of Eos appears twice, and once as a flip card for some reason
            continue
          for card_faces in item['card_faces']:
            img_uris.append(card_faces['image_uris']['normal'])
          cards[frontName] = {
            "name": frontName,
            "img_uri": img_uris
          }
        except KeyError: # no image
          # cards[name] = {
          #   "name": name
          # }
          print("warning no image found")
    cardData = []
    
    # just get the name from each row
    for rows in csvReader:
      curName = rows['Name']
      try:
        cardData.append(cards[curName])
      except KeyError:
        # double sided cards will be the end of me
        # for now just pass
        pass
    output_file.write(json.dumps(cardData, indent=2))
    # output_file.write(json.dumps(cards, indent=2))

make_json(CSV_FILE_PATH, INPUT_PATH, OUTPUT_PATH)