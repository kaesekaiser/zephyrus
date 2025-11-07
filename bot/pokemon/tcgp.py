import json
import re
from functions import fix


card_image_url = r"https://static.dotgg.gg/pokepocket/card/{expansion}-{number}.webp"
types = "Grass", "Fire", "Water", "Lightning", "Psychic", "Fighting", "Darkness", "Metal", "Dragon", "Colorless"
type_colors = {
    "Colorless": "F3EFE2",
    "Darkness": "014649",
    "Dragon": "D5BB2A",
    "Fighting": "DF9809",
    "Fire": "EB6435",
    "Grass": "AACD36",
    "Lightning": "FEE100",
    "Metal": "B8C3C4",
    "Psychic": "BC7EB3",
    "Water": "71C4EE"
}


expansion_names = {
    "A1": "Genetic Apex",
    "A1a": "Mythical Island",
    "P-A": "Promo-A",
    "A2": "Space-Time Smackdown",
    "A2a": "Triumphant Light",
    "A2b": "Shining Revelry",
    "A3": "Celestial Guardians",
    "A3a": "Extradimensional Crisis",
    "A3b": "Eevee Grove",
    "A4": "Wisdom of Sky and Sea",
    "A4a": "Secluded Springs",
    "B1": "Mega Rising"
}
expansion_packs = {
    "A1": ["Charizard", "Mewtwo", "Pikachu"],
    "A1a": [],
    "P-A": [],
    "A2": ["Dialga", "Palkia"],
    "A2a": [],
    "A2b": [],
    "A3": ["Solgaleo", "Lunala"],
    "A3a": [],
    "A3b": [],
    "A4": ["Ho-Oh", "Lugia"],
    "A4a": [],
    "B1": ["Mega Gyarados", "Mega Blaziken", "Mega Altaria"]
}


class Card:
    def __init__(self, expansion: str, number: int, name: str, rarity: str, **kwargs):
        self.expansion = expansion
        self.number = number
        self.name = name
        self.type = "blank"
        self.rarity = rarity
        self.pack: str = kwargs.get("pack")
        self.variant_of: str = kwargs.get("variant")

    @property
    def id(self):
        return f"{self.expansion}-{str(self.number).rjust(3, '0')}"

    @property
    def image_url(self):
        return card_image_url.format(
            expansion="PROMO" if self.expansion == "P-A" else self.expansion,
            number=str(self.number).rjust(3, '0')
        )

    @property
    def expansion_name(self):
        return expansion_names[self.expansion]

    def all_text(self):
        return self.name


class TrainerCard(Card):
    def __init__(self, expansion: str, number: int, name: str, category: str, description: str, **kwargs):
        super().__init__(expansion, number, name, **kwargs)
        self.type = category
        self.description = description

    def all_text(self):
        return " ".join([self.name, self.description])


class Ability:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


class Move:
    def __init__(self, name: str, energy_cost: list[str], power: int | str = 0, description: str = None):
        self.name = name
        self.energy_cost = energy_cost
        self.power = power
        self.description = description


class PokemonCard(Card):
    def __init__(self, expansion: str, number: int, name: str, type: str, hp: int, stage: int, **kwargs):
        super().__init__(expansion, number, name, **kwargs)
        self.type = type
        self.hp = hp
        self.stage = stage
        self.evolves_from: str = kwargs.get("evolves_from", "")
        self.ability: Ability = Ability(**kwargs.get("ability")) if kwargs.get("ability") else None
        self.moves: list[Move] = [Move(**g) if isinstance(g, dict) else g for g in kwargs.get("moves", [])]
        self.weakness = kwargs.get("weakness")
        self.retreat_cost = kwargs.get("retreat_cost", 0)
        self.ex = kwargs.get("ex", self.name.endswith(" ex"))

    def all_text(self):
        return " ".join(
            [self.name] + (["Ability:", self.ability.name, self.ability.description] if self.ability else []) +
            [j for g in self.moves for j in ([g.name, g.description] if g.description else [g.name])]
        )


class CardSearchQuery:
    def __init__(self, **kwargs):
        self.type: str = kwargs.get("type")
        self.hp: str = kwargs.get("hp")
        self.power: str = kwargs.get("power")
        self.stage: int = kwargs.get("stage")
        self.ex: bool = kwargs.get("ex")
        self.text_match: list[str] = kwargs.get("text_match", [])
        self.original_query: str = kwargs.get("original_query")

    def __str__(self):
        return self.original_query

    @staticmethod
    def from_str(txt: str):
        kwargs = {}
        plaintext = []
        for word in txt.split():
            if match := re.fullmatch(
                    r"type[:=](pokemon|trainer|item|supporter|tool|"+("|".join(g.lower() for g in types))+")", word, re.I):
                kwargs["type"] = match[1].title()
            elif match := re.fullmatch(r"(hp)([<>=:]=?[0-9]+)", word, re.I):
                kwargs["hp"] = match[2].replace(":", "=")
            elif match := re.fullmatch(r"(power|pwr|damage|dmg)([<>=:]=?[0-9]+)", word, re.I):
                kwargs["power"] = match[2].replace(":", "=")
            elif match := re.fullmatch(r"stage[:=]([012]|basic)", word, re.I):
                kwargs["stage"] = int(match[1].lower().replace("basic", "0"))
            elif match := re.fullmatch(r"ex[:=](y(es)?|t(rue)?|n(o)?|f(alse)?|[01])", word.lower()):
                kwargs["ex"] = match[1].startswith("y") or match[1].startswith("t") or match[1] == "1"
            else:
                plaintext.append(word)
        return CardSearchQuery(original_query=txt, text_match=plaintext, **kwargs)

    @staticmethod
    def compare_attribute(card_value: int, search_term: str) -> bool:
        if not isinstance(card_value, int):
            return False
        search_value = int(search_term.strip("<>="))
        if search_term.startswith(">="):
            return card_value >= search_value
        elif search_term.startswith(">"):
            return card_value > search_value
        elif search_term.startswith("<="):
            return card_value <= search_value
        elif search_term.startswith("<"):
            return card_value < search_value
        else:
            return card_value == search_value

    def matches_card(self, card: Card):
        if isinstance(card, TrainerCard):
            return card.type == self.type or (self.type is None and self.hp is None and self.power is None and
                                              self.stage is None and self.ex is None)
        elif isinstance(card, PokemonCard):
            if (self.type is not None and self.type != "Pokemon") and card.type != self.type:
                return False
            if self.hp is not None and not self.compare_attribute(card.hp, self.hp):
                return False
            if self.power is not None and not any([self.compare_attribute(m.power, self.power) for m in card.moves]):
                return False
            if self.stage is not None and card.stage != self.stage:
                return False
            if self.ex is not None and card.ex != self.ex:
                return False
        return True

    def get_matches(self) -> list[Card]:
        all_matches = [g for g in card_dex.values() if not g.variant_of and self.matches_card(g)]
        if self.text_match:
            overlap_lengths = {}
            for card in all_matches:
                total_overlap = len(set(fix(card.all_text()).split("-")).intersection(set(self.text_match)))
                if total_overlap:
                    overlap_lengths[total_overlap] = overlap_lengths.get(total_overlap, []) + [card]
            if not overlap_lengths:
                return []
            if max(overlap_lengths.keys()) != len(self.text_match):
                return []
            return overlap_lengths[max(overlap_lengths.keys())]
        return all_matches


def is_sublist(sublist: list, containing_list: list):
    for n, g in enumerate(containing_list):
        if g == sublist[0]:
            if containing_list[n:n+len(sublist)] == sublist:
                return True
    return False


def name_search(txt: str, include_variants: bool = False) -> list[Card]:
    s = fix(txt)
    overlap_lengths = {}
    for expansion, name in expansion_names.items():
        s = re.sub(r"(?<=-)"+fix(name)+r"(?=-|$)", fix(expansion), re.sub(r"^"+fix(name)+r"(?=-|$)", fix(expansion), s))
    split = s.split("-")
    for id_number, card in card_dex.items():
        if fix(id_number) == s:
            return [card]
        name_overlap = set(fix(card.name).split("-")).intersection(set(split))
        expansion_overlap = set(fix(card.expansion_name).split("-")).intersection(set(split))
        total_overlap = sum(({g: 0.1 for g in expansion_overlap} | {g: 1 for g in name_overlap}).values())
        if total_overlap:
            overlap_lengths[total_overlap] = overlap_lengths.get(total_overlap, []) + [card]
        elif fix(card.expansion) in split:
            overlap_lengths[0] = overlap_lengths.get(0, []) + [card]
    if not overlap_lengths:
        return []
    possible_matches = overlap_lengths[max(overlap_lengths.keys())]
    expansion_match = [k for k, v in expansion_names.items() if fix(k) in split]
    if expansion_match:
        possible_matches = [g for g in possible_matches if g.expansion == expansion_match[0]]
    elif max(overlap_lengths.keys()) == 0:
        return []
    if not (include_variants or all(g.variant_of for g in possible_matches)):
        return [g for g in possible_matches if not g.variant_of]
    return possible_matches


def load_cards(raw_data: dict) -> dict[str, Card]:
    def load_card(card: dict):
        if "variant" in card and "name" not in card:
            return load_card(raw_data[card["variant"]] | card)
        return PokemonCard(**card) if "hp" in card else TrainerCard(**card)

    return {k: load_card(v) for k, v in raw_data.items()}


card_dex = load_cards(json.load(open("pokemon/data/tcgp_cards.json")))
