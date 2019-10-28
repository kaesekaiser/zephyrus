from .techs import *
events = {}


class Event(EvenTech):
    def __init__(self, name: str, prereqs: list, set_vars: dict, event_chances: dict, desc: str, **vocab: list):
        super().__init__(name, prereqs, set_vars, event_chances, desc, **vocab)
        events[self.name.lower()] = self


def generic_extinction(name: str, desc: str, **vocab: list):
    Event(name, [], {"extinct": True}, {}, desc, **vocab)


generic_extinction("asteroid",
                   "In {stardate}, {planet} collided with a {adj} {obj}, resulting in a mass extinction event which "
                   "wiped out all traces of {civ} civilization.",
                   adj=["wandering", "wayward"],
                   obj=["asteroid", "comet", "planetoid"])
generic_extinction("volcano",
                   "In {stardate}, a massive volcanic eruption filled the skies of {planet} with ash and blotted out "
                   "the sun. The ensuing volcanic winter threw the planet's delicate ecosystem wildly out of balance, "
                   "bringing about the end of {civ} civilization.")
generic_extinction("gamma-ray-burst",
                   "In {stardate}, a gamma-ray burst – caused by the explosion of a star roughly {dist} {unit} from "
                   "the {system} system – showered {planet} in high energy electromagnetic radiation. The planet's "
                   "atmospheric ozone layer shielded planetary life from immediate harm, but was dramatically "
                   "depleted in the process. Stripped of its protection against ordinary UV radiation, the planet's "
                   "ecosystem gradually collapsed, ushering in the end of {civ} civilization.",
                   dist=[900 + 100 * g for g in range(80)],
                   unit=["light-years", "parsecs"])
generic_extinction("food-illness",
                   "In {stardate}, a food-borne illness began to spread rapidly through the {civ} population. Less "
                   "than 10% of the {civ} survived the plague, causing a population bottleneck which eventually "
                   "brought about the total collapse of {civ} civilization.")
generic_extinction("overhunting",
                   "Due to the extreme effectiveness of stone tools in hunting {beast}, the {civ} managed to hunt the "
                   "{beast} species to extinction. Being reliant on the {beast} for food, the {civ} then suffered a "
                   "famine which brought about the end of {civ} civilization.")
generic_extinction("overfishing",
                   "As the {civ} population increased, they began to overfish the waters of {planet}. By {stardate}, "
                   "they had driven the {fish} species to extinction. The ensuing famine brought about a total "
                   "collapse of {civ} civilization.")
generic_extinction("crop-failure",
                   "In {stardate}, a combination of {adj} weather and pestilence caused a near-total failure of the "
                   "{crop} crop. Being overreliant on {crop} cultivation for food, the {civ} then suffered a massive "
                   "famine which brought about the end of {civ} civilization.",
                   adj=["inclement", "poor"])
generic_extinction("forest-fire",
                   "In {stardate}, a cooking fire started by one of the {civ} jumped to the forest, where it quickly "
                   "blazed out of control. When the fire finally burned itself out, the forest had been almost "
                   "completely destroyed, disrupting the ecosystem of {planet} enough to cause a total collapse of "
                   "{civ} civilization.")
generic_extinction("war-over-metal",
                   "In {stardate}, due to the growing importance of metal-forged weapons in warfare and the scarcity "
                   "of metal deposits on {planet}, a massive and bloody conflict erupted over control of these "
                   "deposits. Over 80% of the {civ} population was wiped out in the fighting, a loss from which "
                   "{civ} civilization was ultimately unable to recover.")
generic_extinction("city-plague",
                   "In {stardate}, a virulent new plague spread swiftly through the largest and densest centers of "
                   "{civ} population. Living in such close proximity, the city-dwelling {civ} were almost entirely "
                   "wiped out by the disease, a loss from which {civ} civilization was ultimately unable to recover.")
generic_extinction("sea-plague",
                   "In {stardate}, a number of {civ} {people} returned from across the sea bearing symptoms of an "
                   "unfamiliar illness. Having no immunity to the germs that caused the disease, the majority of the "
                   "{civ} population was wiped out by the ensuing plague.",
                   people=["explorers", "traders"])
Event("pets",
      [],
      {},
      {},
      "The {civ} have domesticated a species of small {adj} {animals}. The pets assist their {civ} owners with {task} "
      "in exchange for food and shelter.",
      adj=["flying", "feathered", "fluffy", "furry", "scaly", "winged"],
      animals=["animals", "creatures", "predators"],
      task=["hunting", "navigation", "pest control"])
Event("large-city",
      [],
      {},
      {"city-fortress": 3 / 1000,
       "city-holy": 3 / 1000,
       "city-trade": 3 / 1000},
      "In {stardate}, the {civ} population reached 25 million individuals. "
      "Many of these {live} within permanent cities, the largest of which "
      "is known as {city} and has a population of {pop},000.",
      live=["dwell", "live", "reside"],
      pop=list(range(15, 95)))
Event("conqueror",
      [],
      {},
      {"city-fortress": 10 / 1000},
      "In {stardate}, many of the {adj} {civ} {clans} were united under a single banner by an individual known as "
      "{conqueror}. {new_empire} rules over approximately {percent}% of the entire {civ} population. "
      "{as_usual}, it is governed by {gov}.",
      adj=["disparate", "fractious", "warring"],
      clans=["city-states", "clans", "kingdoms", "tribes", "villages"],
      new_empire=["The resulting empire has its capital at {city} and",
                  "The city of {city} {was_made} the capital of the resulting empire, which"],
      was_made=["has become", "has been declared", "has been made", "has been named"],
      percent=list(range(5, 45)),
      as_usual=["Like many other {civ} states", "Unusually for the {civ}"],
      gov=["a council of {leaders}", "a hereditary monarch", "an elected tyrant", "direct democratic vote"],
      leaders=["aristocrats", "clerics", "elders", "oligarchs", "war leaders"])
Event("religion",
      [],
      {},
      {"city-holy": 10 / 1000},
      "In {stardate}, {a_new} religion known as {religion} {became} the official religion of the largest {civ} state. "
      "Adherents of {religion} wear {adj1} {things} to mark themselves as believers.",
      a_new=["a rapidly growing", "an emerging"],
      became=["became", "was declared"],
      adj1=["{distinctive} {adj2}", "{plain} {adj3}", "{adj4}"],
      things=["caps", "cloaks", "clothes", "clothing", "coats", "fabrics", "hats", "hoods", "masks", "robes", "shawls"],
      distinctive=["distinctive", "striking"],
      adj2=["beaded", "black", "blue", "brown", "dark", "embroidered", "gray", "green", "patterned", "purple",
            "scarlet", "red", "white"],
      plain=["plain", "simple"],
      adj3=["black", "blue", "brown", "dark", "gray", "green", "purple", "scarlet", "red", "white"],
      adj4=["brightly colored", "{adj5} colorful", "{adj6}concealing",
            "elaborately decorated", "intricately patterned"],
      adj5=["dazzingly", "distinctive"],
      adj6=["distinctive ", ""])
Event("city-fortress",
      ["large-city"],
      {},
      {"city-holy": -1,
       "city-trade": -1},
      "Following a long series of failed attempts to {attack} the city, {city} has become renowned among the {civ} as "
      "an impenetrable fortress. The image of its distinctive {walls} has been widely adopted in {civ} {art} as a "
      "symbol of {safety}.",
      attack=["attack", "besiege", "capture", "conquer"],
      walls=["gate", "ramparts", "towers", "walls"],
      art=["art", "culture", "literature", "oratory"],
      safety=["resilience", "safety", "strength"])
Event("city-holy",
      ["large-city"],
      {},
      {"city-fortress": -1,
       "city-trade": -1},
      "Due to its role as the birthplace of several major {civ} religions, including the especially prominent "
      "{religion} faith, the city of {city} is regarded by many of the {civ} as a holy site. {detail}",
      detail=["The {pope_of} {city} is considered the de facto leader of the {religion} church as a whole, and "
              "pilgrimages to the city are commonplace.",
              "Leaders from all around the world {visit} the city {to_curry} favor with the leaders of their "
              "people's religion of choice."],
      pope_of=["archbishop of", "high priest of", "highest-ranking {religion} {official} in"],
      official=["bishop", "official", "priest"],
      visit=["journey to", "make trips to", "travel to", "visit"],
      to_curry=["in hopes of currying", "in order to curry"])
Event("city-trade",
      ["large-city"],
      {},
      {"city-fortress": -1,
       "city-holy": -1},
      "The city of {city} has become renowned among the {civ} as a center of commerce and trade. In particular, the "
      "{adj} {stuff_made_there_is} highly sought after by traders around the world.",
      adj=["delicate", "durable", "elegant", "fine", "high-quality", "intricately decorated", "sturdy"],
      stuff_made_there_is=[f"{g} are" if g[-1] == "s" else f"{g} is" for g in  # confusing but this is actually how
                           ["armor", "ceramics", "clothing", "fabrics", "glassware",  # the source code does it
                            "jewelry", "pottery", "textiles", "weapons"]])
generic_extinction("bioterrorism",
                   "In {stardate}, a genetically engineered virus designed as a highly lethal weapon of biological "
                   "warfare was deliberately distributed in several major centers of {civ} population by an agent or "
                   "agents of unknown affiliation. {civ} medical science proved insufficient to combat the ensuing "
                   "plague, which wiped out all but a few isolated pockets of {civ} population and brought an end to "
                   "the era of {civ} technological civilization.")
Event("world-government",
      [],
      {},
      {"nuclear-weapons": -1,
       "nuclear-strike": -1,
       "nuclear-war": -1},
      "In {stardate}, following decades of negotiation, the various sovereign {civ} nations came to an agreement "
      "concerning the establishment of a unified planet-wide government for all of the {civ}.")
Event("nuclear-weapons",
      ["flight", "nuclear-physics", "rocketry"],
      {},
      {"nuclear-strike": 1 / 90,
       "nuclear-war": 1 / 90,
       "skynet": 1 / 90},
      "In {stardate}, the {civ} successfully detonated their first prototype nuclear weapon. It remains unclear "
      "whether the {civ} scientists who worked on the bomb understand the sheer destructive potential of the weapon "
      "they have created.")
Event("nuclear-strike",
      [],
      {},
      {"nuclear-war": 1 / 90},
      "In {stardate}, a single nuclear weapon was deployed in an attack n a {size} {civ} city. The incident did not "
      "escalate into a full-scale nuclear war, but the city was almost completely obliterated, resulting in the "
      "deaths of some {pop},000 {civ}.",
      size=["small", "medium-sized", "large", "major"],
      pop=list(range(50, 250)))
generic_extinction("nuclear-war",
                   "In {stardate}, an early warning system employed by one of the major {civ} superpowers detected an "
                   "incoming nuclear attack. Whether the alert was a false alarm remains unclear, but the "
                   "resulting nuclear counterattack and ensuing full-scale nuclear war has plunged {planet} into a "
                   "state of nuclear winter from which it is unlikely that {civ} civilization will ever recover.")
Event("skynet",
      ["artificial intelligence"],
      {"extinct": True},
      {},
      "In {stardate}, an artificially intelligent agent with command authority over the military forces of a major "
      "{civ} nation spontaneously turned against its {civ} masters. Within weeks, the thoroughly unprepared {civ} "
      "were all but exterminated in a seemingly endless wave of attacks by brutally efficient military machines.")
generic_extinction("gray-goo",
                   "In {stardate}, a swarm of self-replicating {civ} nanobots began to replicate uncontrollably, "
                   "devouring vast swaths of {planet} at a rate which {civ} scientists had formerly deemed impossible. "
                   "After several days of rapid expansion, the swarm seems to have become dormant, but not before "
                   "consuming approximately 5% of the entire mass of {planet} and rendering {civ} civilization "
                   "completely extinct.")
