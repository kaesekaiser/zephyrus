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
    "PROMO": "Promo-A"
}


class Card:
    def __init__(self, expansion: str, number: int, name: str, **kwargs):
        self.expansion = expansion
        self.number = number
        self.name = name
        self.variant_of: str = kwargs.get("variant")

    @property
    def id(self):
        return f"{self.expansion}-{str(self.number).rjust(3, '0')}"

    @property
    def image_url(self):
        return card_image_url.format(expansion=self.expansion, number=str(self.number).rjust(3, '0'))


class TrainerCard(Card):
    def __init__(self, expansion: str, number: int, name: str, category: str, description: str, **kwargs):
        super().__init__(expansion, number, name, **kwargs)
        self.category = category
        self.description = description


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
        self.ex = kwargs.get("ex", False)


def is_sublist(sublist: list, containing_list: list):
    for n, g in enumerate(containing_list):
        if g == sublist[0]:
            if containing_list[n:n+len(sublist)] == sublist:
                return True
    return False


def card_search(txt: str, include_variants: bool = False) -> list[Card]:
    s = fix(txt)
    overlap_lengths = {}
    for expansion, name in expansion_names.items():
        s = re.sub(r"(?<=-)"+fix(name)+r"(?=-|$)", fix(expansion), re.sub(r"^"+fix(name)+r"(?=-|$)", fix(expansion), s))
    split = s.split("-")
    for id_number, card in card_dex.items():
        if fix(id_number) == s:
            return [card]
        if include_variants or not card.variant_of:
            overlap = set(fix(card.name).split("-")).intersection(set(split))
            if overlap:
                overlap_lengths[len(overlap)] = overlap_lengths.get(len(overlap), []) + [card]
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
    return possible_matches


def load_cards(raw_data: dict) -> dict[str, Card]:
    def load_card(card: dict):
        if "variant" in card and "name" not in card:
            return load_card(raw_data[card["variant"]] | card)
        return PokemonCard(**card) if "hp" in card else TrainerCard(**card)

    return {k: load_card(v) for k, v in raw_data.items()}


card_dex = load_cards(json.load(open("pokemon/data/tcgp_cards.json")))
