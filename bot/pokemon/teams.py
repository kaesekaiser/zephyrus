from pokemon.treemons import *
male, female, genderless = 1, -1, 0

teamdict = {  # mondat!
    "Test": (
        mondat(id="Porygon-Z", nick="Tester I", ability="Immortality", moves=["Wake-Up Slap", "Knock Off", "Dragon Rage"]),
        mondat(id="Porygon-Z", nick="Tester II", ability="Immortality"),
        mondat(id="Porygon-Z", nick="Tester III", ability="Immortality"),
        mondat(id="Porygon-Z", nick="Tester IV", ability="Immortality"),
        mondat(id="Porygon-Z", nick="Tester V", ability="Immortality"),
        mondat(id="Porygon-Z", nick="Tester VI", ability="Immortality")
    ),
    "Testing": (
        mondat(id="Smeargle", nick="Testing I", ability="Multitype", helditem="Draco Plate"),
        mondat(id="Smeargle", nick="Tester II", ability="Immortality"),
        mondat(id="Smeargle", nick="Tester III", ability="Immortality"),
        mondat(id="Smeargle", nick="Tester IV", ability="Immortality"),
        mondat(id="Smeargle", nick="Tester V", ability="Immortality"),
        mondat(id="Smeargle", nick="Tester VI", ability="Immortality"),
    ),
    "DPCynthia": (
        mondat(id="Spiritomb", lvl=61, gender=female, ability="Pressure", moves=["Dark Pulse", "Psychic", "Silver Wind", "Embargo"]),
        mondat(id="Roserade", lvl=60, gender=female, ability="Natural Cure", moves=["Energy Ball", "Sludge Bomb", "Shadow Ball", "Extrasensory"]),
        mondat(id="Gastrodon", lvl=60, gender=female, ability="Sticky Hold", moves=["Muddy Water", "Earthquake", "Stone Edge", "Sludge Bomb"]),
        mondat(id="Lucario", lvl=63, gender=male, ability="Steadfast", moves=["Aura Sphere", "Dragon Pulse", "Psychic", "Earthquake"]),
        mondat(id="Milotic", lvl=63, gender=female, ability="Marvel Scale", moves=["Surf", "Ice Beam", "Mirror Coat", "Aqua Ring"]),
        mondat(id="Garchomp", lvl=66, gender=female, ability="Sand Veil", helditem="Sitrus Berry", moves=["Dragon Rush", "Earthquake", "Brick Break", "Giga Impact"])
    ),
    "SunRun": (
        mondat(id="Blastoise", nick="Adam", helditem="Blastoisinite"),
        mondat(id="Ditto", nick="Fuckwad", gender=genderless, ability="Imposter"),
        mondat(id="Arcanine", nick="Growlet", lvl=63, gender=female, ability="Flash Fire", helditem="Firium Z", nature="Mild", moves=["Transform", "Reversal", "Flamethrower", "Flame Burst"]),
        mondat(id="Alolan Raichu", nick="Jupiter", lvl=65, gender=male, ability="Surge Surfer", helditem="Aloraichium Z", nature="Bold", moves=["Thunderbolt", "Psychic", "Nasty Plot", "Psyshock"]),
        mondat(id="Decidueye", nick="Rowlithe", lvl=63, gender=female, ability="Overgrow", helditem="Decidium Z", nature="Gentle", moves=["Leaf Blade", "Feather Dance", "Spirit Shackle", "Shadow Ball"]),
        mondat(id="Gigalith", nick="Joplin", lvl=64, gender=female, ability="Sturdy", helditem="Rockium Z", nature="Quiet", moves=["Iron Defense", "Rock Slide", "Earthquake", "Stone Edge"]),
        mondat(id="Vaporeon", nick="Aquamarine", lvl=64, gender=female, ability="Water Absorb", helditem="Waterium Z", nature="Lax", moves=["Surf", "Aqua Ring", "Ice Beam", "Acid Armor"]),
        mondat(id="Hariyama", nick="Duke", lvl=62, gender=male, ability="Thick Fat", helditem="Fightinium Z", nature="Impish", moves=["Knock Off", "Brick Break", "Wake-Up Slap", "Poison Jab"]),
    ),
    "Red": (
        mondat(id="Pikachu", lvl=88, gender=male, ability="Static", helditem="Light Ball", moves=["Volt Tackle", "Iron Tail", "Quick Attack", "Thunderbolt"]),
        mondat(id="Lapras", lvl=80, gender=male, ability="Shell Armor", moves=["Body Slam", "Brine", "Blizzard", "Psychic"]),
        mondat(id="Snorlax", lvl=82, gender=male, ability="Thick Fat", moves=["Shadow Ball", "Crunch", "Blizzard", "Giga Impact"]),
        mondat(id="Venusaur", lvl=84, gender=male, ability="Overgrow", moves=["Frenzy Plant", "Giga Drain", "Sludge Bomb", "Sleep Powder"]),
        mondat(id="Charizard", lvl=84, gender=male, ability="Blaze", moves=["Blast Burn", "Flare Blitz", "Air Slash", "Dragon Pulse"]),
        mondat(id="Blastoise", lvl=84, gender=male, ability="Torrent", moves=["Hydro Cannon", "Blizzard", "Flash Cannon", "Focus Blast"])
    ),
    "Arin": (
        mondat(id="Dugtrio", nick="Buttnuttz!", lvl=35, gender=male, moves=["Dig", "Fury Swipes", "Mud-Slap", "Sand Tomb"]),
        mondat(id="Pikachu", nick="SPLAART!!!", lvl=27, gender=female, ability="Static", moves=["Thunderbolt", "Quick Attack", "Slam", "Thunder Wave"]),
        mondat(id="Charmeleon", nick="Sch", lvl=34, gender=male, ability="Blaze", moves=["Scratch", "Flamethrower", "Ember", "Metal Claw"]),
        mondat(id="Graveler", nick="TurntSNACO", lvl=32, gender=male, moves=["Self-Destruct", "Strength", "Magnitude", "Rock Throw"]),
        mondat(id="Vileplume", nick="Fuck King", lvl=34, gender=female, moves=["Giga Drain", "Sleep Powder", "Poison Powder", "Acid"]),
        mondat(id="Beedrill", nick="Buntd,", lvl=38, gender=male, moves=["Pursuit", "Cut", "Twineedle", "Pin Missile"]),
    ),
    "Koga": (
        mondat(id="Koffing", ability="Levitate", lvl=37, gender=male, moves=["Self-Destruct", "Sludge", "Smokescreen", "Toxic"]),
        mondat(id="Muk", ability="Sticky Hold", lvl=39, gender=male, moves=["Minimize", "Sludge", "Acid Armor", "Toxic"]),
        mondat(id="Koffing", nick="Koffing II", ability="Levitate", lvl=37, gender=male, moves=["Self-Destruct", "Sludge", "Smokescreen", "Toxic"]),
        mondat(id="Weezing", ability="Levitate", lvl=43, gender=male, moves=["Tackle", "Sludge", "Smokescreen", "Toxic"])
    ),
    "A": [mondat(id="Boss", ability="Magic Guard", lvl=70)],
    "TreeThree": ("TREE", 3)
}
