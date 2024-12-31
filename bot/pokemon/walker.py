from pokemon.raids import *
from random import choices


evolutionary_stones = {
    "Fire Stone": fire,
    "Water Stone": water,
    "Thunder Stone": electric,
    "Leaf Stone": grass,
    "Moon Stone": dark,
    "Sun Stone": fire,
    "Shiny Stone": fairy,
    "Dusk Stone": ghost,
    "Dawn Stone": psychic,
    "Ice Stone": ice
}
other_evo_items = {
    "King's Rock": {rock: 200},
    "Metal Coat": {steel: 200},
    "Dragon Scale": {dragon: 200},
    "Upgrade": {electric: 200},
    "Deep Sea Scale": {water: 100, fairy: 100},
    "Deep Sea Tooth": {water: 100, dark: 100},
    "Prism Scale": {fairy: 200},
    "Protector": {rock: 100, steel: 100},
    "Electirizer": {electric: 200},
    "Magmarizer": {fire: 200},
    "Dubious Disc": {electric: 100, psychic: 100},
    "Oval Stone": {normal: 200},
    "Razor Claw": {dark: 100, steel: 100},
    "Razor Fang": {dark: 100, rock: 100},
    "Reaper Cloth": {ghost: 100, dark: 100},
    "Sachet": {fairy: 200},
    "Whipped Dream": {fairy: 100, ice: 100},
    "Sweet Apple": {grass: 200},
    "Tart Apple": {grass: 200},
    "Syrupy Apple": {grass: 200},
    "Auspicious Armor": {psychic: 200},
    "Malicious Armor": {ghost: 200}
}
walker_items = [
    *types, *evolutionary_stones.keys(), "Alola Stone", "Galar Stone", "Hisui Stone", *other_evo_items.keys()
]


class Charm:
    def __init__(self, name: str, id_no: int, emote: str, desc: str,
                 price: dict[str, int], effects: dict[str, int | float],
                 prereqs: dict[str] = (), replaces: int = None):
        self.name = name
        self.id = id_no
        self.emote = emote
        self.desc = desc
        self.price = price
        self.effects = effects
        self.prereqs = prereqs if prereqs else {}
        self.replaces = replaces

    @staticmethod
    def from_json(js: dict):
        return Charm(**js)

    @property
    def json(self):
        return {
            "name": self.name, "id_no": self.id, "emote": self.emote, "desc": self.desc, "price": self.price,
            "prereqs": self.prereqs, "replaces": self.replaces
        }

    def odds_for(self, mon: BareMiniMon, base_odds: float):
        ret = 1
        for t in mon.types:
            if t in self.effects:
                ret *= self.effects[t]
        if self.effects.get("starter") and mon.species.name in starters:
            ret *= self.effects["starter"]
        if self.effects.get("rarity"):
            ret *= 0.85 + 0.75 / base_odds  # "flattens the curve" of the encounter distribution
        return ret


class Locale:
    def __init__(self, name: str, id_no: int, desc: str, mons: dict, unlock_level: int):
        self.name = name
        self.id = id_no
        self.desc = desc
        self.mons = mons
        self.unlock_level = unlock_level

    @property
    def bare_mini_mons(self):
        return {get_saf(g): j for g, j in self.mons.items()}

    @staticmethod
    def from_json(js: dict):
        return Locale(js["name"], js["id"], js["desc"], js["mons"], js.get("unlock_level", 1))

    @property
    def encounter_table(self):
        return {
            "Very Common": [g for g, j in self.mons.items() if j >= 8],
            "Common": [g for g, j in self.mons.items() if 8 > j >= 3],
            "Uncommon": [g for g, j in self.mons.items() if 3 > j > 1],
            "Rare": [g for g, j in self.mons.items() if j <= 1],
        }

    def get_rarity(self, mon: BareMiniMon | str, return_exact_odds: bool = False):
        rarities = {j: (self.mons[j] if return_exact_odds else k) for k, v in self.encounter_table.items() for j in v}
        if isinstance(mon, str):
            mon = get_saf(mon)
        return rarities.get(mon.species_and_form, rarities.get(mon.name, rarities.get(f"{mon.species.name}-Random")))

    def charmed_odds(self, active_charms: list[Charm]) -> dict[BareMiniMon, float]:
        return {g: product([j, *(c.odds_for(g, j) for c in active_charms)]) for g, j in self.bare_mini_mons.items()}

    def encounter(self, active_charms: list[Charm] = ()) -> BareMiniMon:
        return choices(list(self.bare_mini_mons), weights=list(self.charmed_odds(active_charms).values()), k=1)[0]


walker_exp_levels = [0, 500, 1200, 2000, 3000, 4500, 6500, 9000, 12000]


def walker_level_desc(n: int) -> str:
    ret = [f"\\- **{len([g for g in walker_locales.values() if g.unlock_level <= n])}** stroll locales."]
    if n >= 3:
        ret.append(
            f"\\- {'**' if n in [3, 5, 7] else ''}Type Charms {'I' * min((n - 1) // 2, 3)}: Increase the spawn "
            f"rates of Pok\u00e9mon of their type by {2 * min((n - 1) // 2, 3)}x.{'**' if n in [3, 5, 7] else ''}"
        )
    if n >= 4:
        ret.append(
            f"\\- {'**' if n in [4, 6, 8] else ''}Candied Charm {'I' * min(n // 2 - 1, 3)}: Increases the token reward "
            f"for catching a Pok\u00e9mon by {min(n // 2, 4)}x.{'**' if n in [4, 6, 8] else ''}"
        )
    if n >= 6:
        ret.append(
            f"\\- {'**' if n == 6 else ''}Capture Charm: Increases the catch rate of wild Pok\u00e9mon."
            f"{'**' if n == 6 else ''}"
        )
    if n >= 8:
        ret.append(
            f"\\- {'**' if n == 8 else ''}Oaken Charm: Increases the spawn rates of starter Pok\u00e9mon by 10x."
            f"{'**' if n == 8 else ''}"
        )
    if n >= 9:
        ret.append(
            f"\\- {'**' if n == 9 else ''}Rarity Charm: Increases the spawn rates of rare and uncommon Pok\u00e9mon."
            f"{'**' if n == 9 else ''}"
        )
    return "\n".join(ret)


def walker_level_up_rewards(n: int) -> str:
    ret = [f"\\- Unlocked **{len([g for g in walker_locales.values() if g.unlock_level == n])}** new stroll locales!"]
    if n >= 3:
        ret.extend({
            3: ["\\- Unlocked the **Type Charms!** They boost the spawn rates of their respective types by 2x."],
            4: ["\\- Unlocked the **Candied Charm!** It doubles your token rewards for catching Pok\u00e9mon."],
            5: ["\\- Unlocked the **Type Charms II!** They boost the spawn rates of their respective types by 4x."],
            6: ["\\- Unlocked the **Candied Charm II!** It triples your token rewards for catching Pok\u00e9mon.",
                "\\- Unlocked the **Capture Charm!** It boosts the catch rate of wild Pok\u00e9mon."],
            7: ["\\- Unlocked the **Type Charms III!** They boost the spawn rates of their respective types by 6x."],
            8: ["\\- Unlocked the **Candied Charm III!** It quadruples your token rewards for catching Pok\u00e9mon.",
                "\\- Unlocked the **Oaken Charm!** It boosts the spawn rate of starter Pok\u00e9mon."],
            9: ["\\- Unlocked the **Rarity Charm!** It boosts the spawn rate of uncommon and rare Pok\u00e9mon."]
        }.get(n, []))
        ret.extend(["", "Purchase new charms in the `z!pw market`, and equip them in `z!pw charms`!"])
    return "\n".join(ret)


class WalkerUser:
    def __init__(self, no: int, box: list[list], dex: list[str], tokens: dict[str, int],
                 owned_charm_ids: list[int], equipped_charm_ids: list[int], other_items: dict[str, int], exp: int):
        self.id = no
        self.box = box  # list of mons formatted as [*walker_pack, locale id (int), date (int)]
        self.dex = dex  # list of previously-caught mons (species names only)
        self.tokens = tokens
        self.owned_charm_ids = owned_charm_ids
        self.equipped_charm_ids = equipped_charm_ids
        self.other_items = other_items
        self.exp = exp

    @property
    def owned_charms(self) -> list[Charm]:
        return [charm_ids[g] for g in self.owned_charm_ids]

    @property
    def equipped_charms(self) -> list[Charm]:
        return [charm_ids[g] for g in self.equipped_charm_ids]

    @property
    def unreplaced_charms(self) -> list[Charm]:
        replace = [g.replaces for g in self.owned_charms if g is not None]
        return [g for g in self.owned_charms if g.id not in replace]

    @property
    def all_items(self):
        return {**self.tokens, **self.other_items}

    @property
    def level(self) -> int:
        return max(n for n, g in enumerate(walker_exp_levels) if self.exp >= g) + 1

    def has_of(self, price: dict[str, int]) -> dict[str, int]:
        return {g: self.all_items[g] for g in price.keys() if g in self.all_items}

    def can_afford(self, price: dict[str, int]):
        return all(self.all_items.get(g, 0) >= j for g, j in price.items())

    def catch(self, mon: BareMiniMon, loc: Locale, time: float, token_reward: int = 1):
        self.box.append([*mon.walker_pack, loc.id, round(time // 86400)])
        self.exp += 1
        self.add_to_dex(mon)
        for t in mon.types:
            self.tokens[t] += token_reward

    def add_to_dex(self, mon: BareMiniMon):
        if mon.species.name not in self.dex:
            self.dex.append(mon.species.name)
            self.exp += 20

    def transfer(self, index: int):
        mon = BareMiniMon.from_walker_pack(self.box.pop(index))
        for t in mon.types:
            self.tokens[t] += 1

    def spend(self, items: dict[str, int]):
        for item, amount in items.items():
            if item in types:
                self.tokens[item] -= amount
            else:
                self.other_items[item] -= amount

    def meets_prereqs_for(self, charm_or_locale: Charm | Locale):
        if isinstance(charm_or_locale, Locale):
            return self.level >= charm_or_locale.unlock_level
        else:
            return (charm_or_locale.prereqs.get("charm") in [None, *self.owned_charm_ids]) and \
                self.level >= charm_or_locale.prereqs.get("level", 0)

    def __str__(self):
        box = [
            [BareMiniMon.from_walker_pack(g[:4]).walker_key, g[4], round(g[5] * 100)] for g in self.box
        ]
        box = [f"{rebase(g[0], 10, 62, 3)}{rebase(g[1] + g[2], 10, 62, 4)}" for g in box]
        dex = [rebase(nat_dex_order.index(g), 10, 62, 2) for g in self.dex]
        tokens = [rebase(g, 10, 62, 3) for g in self.tokens.values()]
        owned = [str(g).rjust(2, "0") for g in self.owned_charm_ids]
        equipped = [str(g).rjust(2, "0") for g in self.equipped_charm_ids]
        items = [
            f"{str(walker_items.index(g)).rjust(2, '0')}{rebase(j, 10, 62, 2)}"
            for g, j in self.other_items.items()
        ]
        return f"{self.id}|{''.join(box)}|{''.join(dex)}|{''.join(tokens)}|" \
               f"{''.join(owned)}|{''.join(equipped)}|{''.join(items)}|{rebase(self.exp, 10, 62)}"

    @staticmethod
    def from_str(s: str):
        no = int(s.split("|")[0])
        box = []
        for mon in snip(s.split("|")[1], 7):
            bio = decimal(mon[:3], 62)
            date = decimal(mon[3:], 62)
            box.append([*BareMiniMon.from_walker_key(bio).walker_pack, date % 100, date // 100])
        dex = [nat_dex_order[decimal(g, 62)] for g in snip(s.split("|")[2], 2)]
        tokens = {types[n]: decimal(g, 62) for n, g in enumerate(snip(s.split("|")[3], 3))}
        owned_charms = [int(g) for g in snip(s.split("|")[4], 2)]
        equipped_charms = [int(g) for g in snip(s.split("|")[5], 2)]
        items = {walker_items[int(g[:2])]: decimal(g[2:], 62) for g in snip(s.split("|")[6], 4)}
        exp = decimal(s.split("|")[7], 62)
        return WalkerUser(no, box, dex, tokens, owned_charms, equipped_charms, items, exp)

    @staticmethod
    def new(no: int):
        return WalkerUser(no, [], [], {g: 0 for g in types}, [], [], {}, 0)


with open("pokemon/walker/locales.json", "r") as fp:
    walker_locales = {g: Locale.from_json(j) for g, j in json.load(fp).items()}
walker_locale_ids = {g.id: g for g in walker_locales.values()}


with open("pokemon/walker/charms.json", "r") as fp:
    charms = {g: Charm.from_json(j) for g, j in json.load(fp).items()}
charm_ids = {g.id: g for g in charms.values()}


rarity_stars = {
    "Very Common": "bronze_star",
    "Common": "silver_star",
    "Uncommon": "gold_star",
    "Rare": "diamond_star"
}


walker_evo_overrides = {
    "Espeon": {"Dawn Stone": 1},
    "Umbreon": {"Moon Stone": 1},
    "Sylveon": {"Shiny Stone": 1}
}
cannot_evolve_walker = ["Shedinja"]


def evolution_tokens(mon: BareMiniMon, evo: Evolution):
    into_mon = get_saf(evo.into)
    n = (into_mon.bst // 100 - 1) * 50
    if not mon.evolves_from:
        n = round(n * 0.8)
    if mon.type2:
        n = round(n / 2)

    ret = {}
    for t in mon.types:
        ret[t] = n

    method = evo.first_method

    if method.get("item") in evolutionary_stones or method.get("item") in other_evo_items:
        ret[method["item"]] = 1
    if method.get("holding") in other_evo_items:
        ret[method["holding"]] = 1
    if method.get("location") in ["Alola", "Galar", "Hisui"]:
        ret[method["location"] + " Stone"] = 1

    if evo.into in walker_evo_overrides:
        ret.update(walker_evo_overrides[evo.into])

    return ret


walker_marketplace = {
    "Charms": charms,
    "Stones": {g: {"name": g, "price": {j: 200}} for g, j in evolutionary_stones.items()},
    "Other Items": {g: {"name": g, "price": j} for g, j in other_evo_items.items()}
}
