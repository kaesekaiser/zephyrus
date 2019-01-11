techs = {}


def none_list(l: list):
    return ", ".join(l) if len(l) > 0 else "none"


def cap_name(s: str):
    def cap_word(st: str):
        return st.upper() if st.upper() == "FTL" else st.title()
    return " ".join([cap_word(g) for g in s.split()])


class EvenTech:  # unified class for both techs and events, since they're functionally almost identical
    def __init__(self, name: str, prereqs: list, set_vars: dict, event_chances: dict, desc: str, **vocab: list):
        self.name = name
        self.prereqs = tuple(prereqs)
        self.setVars = set_vars
        self.eventChances = event_chances
        self.desc = desc
        self.vocab = vocab


class Tech(EvenTech):
    def __init__(self, name: str, prereqs: list, set_vars: dict, event_chances: dict, desc: str, **vocab: list):
        super().__init__(name, prereqs, set_vars, event_chances, desc, **vocab)
        techs[self.name.lower()] = self


Tech("toolmaking",
     [],
     {},
     {"overhunting": 4 / 1000,
      "overfishing": -3 / 1000,
      "crop-failure": -3 / 1000,
      "food-illness": 1 / 1000,
      "pets": 3 / 1000,
      "conqueror": 1 / 1000},
     "The {civ} {use} stone tools {fr}{joiner} hunting the wild {beast}.",
     use=["make extensive use of", "make use of", "make widespread use of ", "use"],
     fr=["for many things", "in a variety of contexts"],
     joiner=[", especially when", ", including as weapons when", ", including when",
             ". This has dramatically improved their efficiency in"])
Tech("agriculture",
     [],
     {},
     {"overhunting": -3 / 1000,
      "overfishing": -3 / 1000,
      "crop-failure": 4 / 1000,
      "pets": 4 / 1000},
     "The {civ} have begun to cultivate crops{including} {the_crop}.",
     including=[", including", ". One especially popular crop is", ". They are especially fond of"],
     the_crop=["a kind of {adj} {plant} known as {crop}{detail}", "{crop}, a kind of {adj} {plant}{detail}"],
     adj=["bitter", "chewy", "colorful", "fleshy", "hardy", "sour", "sweet", "tasty", "tough"],
     plant=["cactus", "flower", "fruit", "fungus", "grain", "leaf", "lichen", "moss",
            "mushroom", "nut", "root", "seaweed", "seedpod", "stalk", "vegetable", "vine"],
     detail=["", "", " that grows well {in_biome} of {planet}"],
     in_biome=["in the {biome_a}", "on the {biome_b}"],
     biome_a=["dense forests", "deserts", "dominant climate", "fertile soil", "forests",
              "grasslands", "jungles", "soil", "rainforests", "rocky soil", "scrublands"],
     biome_b=["floodplains", "plains", "riverbanks"])
Tech("fishing",
     [],
     {},
     {"overhunting": -3 / 1000,
      "overfishing": 4 / 1000,
      "crop-failure": -3 / 1000,
      "food-illness": 1 / 1000},
     "The {civ} have learned how to catch water-dwelling creatures such as the {fish}, "
     "which is now {an_important} part of the {civ} diet.",
     an_important=["an important", "a staple"])
Tech("writing",
     [],
     {"techChance": 1 / 60},
     {"war-over-metal": -1 / 1000,
      "conqueror": 3 / 1000,
      "religion": 1 / 1000},
     "The {civ} have developed a simple system of writing, which they use primarily for {purpose}.",
     purpose=["poetry", "record-keeping", "storytelling", "worship"])
Tech("astronomy",
     [],
     {},
     {"religion": 1 / 1000},
     "The {civ} have begun to watch the stars and recognize patterns in the movements of stars, "
     "which they use to navigate over great distances and keep track of time.")
Tech("fire",
     ["toolmaking"],
     {},
     {"forest-fire": 2 / 1000,
      "food-illness": -3 / 1000},
     "{intro} {civ} have mastered the control of fire. They use it to cook their food, "
     "and to light their villages at night.",
     intro=["{despite} a few {early} mishaps, the", "The", "The"],
     despite=["Despite", "In spite of"],
     early=["early", "initial"])
Tech("metalworking",
     ["fire"],
     {},
     {"war-over-metal": 3 / 1000,
      "conqueror": 4 / 1000},
     "The {civ} have discovered how to forge molten metal into jewelry, tools, weapons, and armor.")
Tech("construction",
     ["toolmaking", "agriculture"],
     {},
     {"large-city": 1 / 1000,
      "city-plague": 2.5 / 1000,
      "war-over-metal": -1 / 1000,
      "forest-fire": -2 / 1000,
      "conqueror": 2 / 1000,
      "pets": 1 / 1000,
      "religion": 3 / 1000},
     "The {civ} have begun to construct permanent dwellings and other structures{using} {mat} as a building material.",
     using=[", making especially extensive use of", ". They make especially extensive use of",
            ". They seem to favor", ". Wherever possible, they seem to prefer"],
     mat=["brick", "bricks", "clay", "limestone", "marble", "sandstone", "stone",
          "the wood of the {crop} plant", "wood"])
Tech("mathematics",
     ["writing", "astronomy"],
     {},
     {},
     "The {civ} have developed a sophisticated understanding of basic mathematics, such as "
     "arithmetic, algebra, and geometry.")
Tech("sailing",
     ["astronomy", "construction"],
     {},
     {"sea-plague": 2 / 1000,
      "large-city": 1 / 1000,
      "war-over-metal": -2 / 1000,
      "city-trade": 7 / 1000},
     "The {civ} have learned how to build ships and sail them across the oceans of {planet} to explore "
     "and trade over increasingly greater distances.")
Tech("architecture",
     ["construction", "mathematics"],
     {},
     {"large-city": 5 / 1000,
      "city-fire": -1 / 1000,
      "religion": 5 / 1000},
     "The {civ} have begun to make use of more sophisticated construction techniques, relying on sturdy structural "
     "elements such as arches and buttresses to support larger and larger buildings.")
Tech("plumbing",
     ["construction", "metalworking"],
     {},
     {"large-city": 3 / 1000,
      "city-plague": -2 / 1000,
      "sea-plague": -1 / 1000},
     "The {civ} have built elaborate pipe and sewer systems to supply their larger settlements, such "
     "as {city}, with fresh water and a hygenic means of waste disposal.")
Tech("optics",
     ["mathematics", "metalworking"],
     {},
     {},
     "The {civ} have begun to use lenses and mirrors made from polished crystal, glass, and water "
     "to redirect and focus light.")
Tech("alchemy",
     ["mathematics", "metalworking"],
     {},
     {},
     "Some of the {civ} have begun to experiment with alchemy, systematically searching for new ways of "
     "combining and manipulating ingredients to yield useful chemicals, compounds, and medicines.")
Tech("mill power",
     ["metalworking", "sailing"],
     {},
     {},
     "The {civ} have begun to construct wind and water mills, which redirect the forces of the natural world to "
     "perform repetitive mechanical tasks such as grinding grain and pumping water.")
Tech("gunpowder",
     ["alchemy"],
     {},
     {},
     "The {civ} have discovered a way to manufacture gunpowder, which they primarily use {in_context}.",
     in_context=["in warfare", "for explosive mining"])
Tech("the printing press",
     ["architecture", "metalworking"],
     {"techChance": 1 / 30},
     {},
     "The {civ} have developed a simple printing press, and mass-produced versions of important texts have begun to "
     "circulate widely throughout the world. {texts_are} especially popular.",
     texts_are=["Light novels are", "Philosophical texts are", "Poetry is", "Political pamphlets are",
                "Religious texts are", "Romance novels are", "Satire is", "Scary stories are", "Serial fiction is",
                "Tales of heroism are", "Transcriptions of folktales are", "Works of natural philosophy are"])
Tech("taxonomy",
     ["alchemy", "optics", "the printing press"],
     {},
     {},
     "Through systematic observation and categorization of the various living things on {planet}, the {civ} have begun "
     "to develop a more sophisticated understanding of biology. Some theorists have even put forth the idea that "
     "dramatically different-looking organisms, such as the {beast} and the {fish}, may in fact {share} a single "
     "common ancestor.",
     share=["be descended from", "share"])
Tech("calculus",
     ["optics", "the printing press"],
     {},
     {},
     "In their efforts to understand the motion of planets in the sky, free-falling bodies, and projectiles, the {civ} "
     "have developed a new branch of mathematics which is immediately recognizable as calculus.")
Tech("rocketry",
     ["calculus", "gunpowder"],
     {},
     {},
     "The {civ} have begun to develop rockets.")
Tech("steam power",
     ["architecture", "mill power"],
     {},
     {},
     "The {civ} have developed a practical and cost-effective steam engine, which can be fueled with wood or coal.")
Tech("electromagnetism",
     ["alchemy", "architecture", "mill power", "the printing press"],
     {},
     {},
     "The {civ} have successfully tamed electricity, and are now beginning to deploy it throughout society. Electric "
     "lights are widespread, electric motors are used to drive factories, and the growing need for electric power has "
     "led to the construction of power plants near every major center of {civ} population.")
Tech("telegraphy",
     ["electromagnetism", "steam power"],
     {},
     {},
     "The {civ} have begun harnessing the power of electricity to send messages across very great distances with "
     "unprecedented speed. Due to the overhead of encoding and decoding messages, long-distance communication remains "
     "far from instantaneous, but it is now possible for individuals on opposite sides of {planet} to exchange several "
     "messages over the course of a single day.")
Tech("flight",
     ["calculus", "electromagnetism", "steam power"],
     {},
     {},
     "The {civ} have developed flying machines which can carry them into the skies above {planet}.")
Tech("transistors",
     ["calculus", "electromagnetism", "steam power"],
     {},
     {},
     "With the development of the transistor, the {civ} have begun to construct more sophisticated "
     "electronic circuits.")
Tech("germ theory",
     ["calculus", "taxonomy"],
     {},
     {"city-plague": -1 / 1000,
      "sea-plague": -1 / 1000},
     "{the} {idea} that diseases {are} caused by microorganisms has begun to catch on among the {civ}, leading to "
     "the widespread adoption of public health policies which have greatly reduced the spread of disease.",
     the=["Although initially controversial, the", "The initially controversial", "The"],
     idea=["hypothesis", "idea", "theory"],
     are=["are", "can be"])
Tech("genetics",
     ["germ theory"],
     {},
     {"bioterrorism": 1 / 360},
     "The {civ} have arrived at a sophisticated understanding of genetics, which has enabled them to craft new forms "
     "of life by deliberately modifying the genes of existing organisms.")
Tech("nuclear physics",
     ["calculus", "gunpowder", "telegraphy"],
     {},
     {"nuclear-weapons": 1 / 30},
     "The {civ} have developed an accurate model of the internal structure of the atom, which has also enabled them "
     "to understand the phenomenon of radioactivity.")
Tech("mass media",
     ["calculus", "telegraphy"],
     {},
     {},
     "The {civ} have discovered that electromagnetic waves may be used to transmit information, enabling the "
     "development and widespread deployment of media for audiovisual broadcasting.")
Tech("digital computers",
     ["transistors"],
     {},
     {},
     "The {civ} have begun to build general-purpose programmable computers.")
Tech("quantum physics",
     ["nuclear physics"],
     {},
     {},
     "The {civ} have begun to understand quantum physics.")
Tech("spaceflight",
     ["digital computers", "flight", "rocketry"],
     {},
     {"asteroid": -1 / 2000},
     "The {civ} have taken their first tentative steps into space, launching craft capable of supporting several "
     "individuals into orbit around {planet} before retrieving them safely.")
Tech("networked computers",
     ["digital computers", "mass media"],
     {"techChance": 1 / 20},
     {"world-government": 1 / 90},
     "The {civ} have begun to connect their computers into a single vast network, enabling communication and "
     "collaboration on a truly global scale.")
Tech("artificial intelligence",
     ["networked computers"],
     {},
     {"skynet": 1 / 180,
      "fortnite": 1 / 1000},
     "The {civ} have developed a form of artificial general intelligence which rivals many of their own "
     "intellectual capabilities.")
Tech("nanotechnology",
     ["networked computers", "quantum physics"],
     {},
     {"gray-goo": 1 / 180},
     "The {civ} have begun to experiment with the use of \"intelligent materials\", in the form of swarms of "
     "programmable nanobots.")
Tech("space colonization",
     ["nanotechnology", "networked computers", "spaceflight"],
     {},
     {"asteroid": -1,
      "volcano": -1,
      "world-government": 2 / 90},
     "The {civ} have begun to establish permanent colonies on worlds other than {planet}. Although still largely "
     "unable to travel outside of the {system} system, the distribution of {civ} civilization across multiple worlds "
     "greatly reduces the risk that they will collapse due to any crisis of merely planetary scale.")
Tech("quantum computers",
     ["networked computers", "quantum physics"],
     {},
     {},
     "The {civ} have constructed their first cost-effective quantum computers, dramatically improving their "
     "collective ability to perform certain types of calculation.")
Tech("FTL communication",
     ["artificial intelligence", "quantum computers"],
     {},
     {},
     "Through their investigations of quantum phenomena, the {civ} have discovered a means of sending and receiving "
     "messages which travel at speeds exceeding that of light itself.")
Tech("FTL travel",
     ["FTL communication", "space colonization"],
     {"victorious": True},
     {},
     "The {civ} have successfully tested their first faster-than-light starship. No longer are they trapped within "
     "the gravity well of the {system} system: they are now free to take their place alongside us as fellow wanderers "
     "among the stars.")
