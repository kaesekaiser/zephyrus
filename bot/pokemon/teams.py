from pokemon.mons import *


class Team:
    def __init__(self, name: str):
        self.name = name
        self.mons = []  # list of packed mons
        self.reflect = 0
        self.light_screen = 0
        self.aurora_veil = 0

    def add(self, mon: Mon):
        if len(self.mons) < 6:
            if mon:
                mon.team_position = len(self.mons)
                self.mons.append(mon.pack)
        else:
            raise ValueError("Team already has six mons.")

    def remove(self, mon: Mon | int):
        if self.mons:
            if isinstance(mon, Mon):
                self.mons.remove(mon)
            else:
                self.mons.pop(mon)
            self.update_pos_values()

    def clear(self):
        self.mons.clear()

    def copy(self):
        ret = Team(self.name)
        for mon in self.mons:
            ret.add(Mon.unpack(mon))
        return ret

    def update_pos_values(self):
        for i in range(len(self.mons)):
            self.mons[i]["pos"] = i + 1

    def has_mon(self, query: str | int, query_type: str = "spc") -> int:
        """Like Mon.has_move(), returns the position (1-6) of a mon in the team, if one exists; else, returns 0."""
        if isinstance(query, str):
            ret = [n for n, g in enumerate(self.mons) if g[query_type].lower() == query.lower()]
        else:
            if query_type == "spc":
                return query
            ret = [n for n, g in enumerate(self.mons) if g[query_type] == query]
        if len(ret) > 1:
            raise ValueError("Multiple mons meet the criterion.")
        return 0 if not ret else (ret[0] + 1)

    def get_mon(self, query: str | int, query_type: str = "spc") -> dict:
        if has := self.has_mon(query, query_type):
            return self.mons[has - 1]
        raise ValueError("No mon found.")

    @property
    def unpacked_mons(self):
        return [Mon.unpack(g) for g in self.mons]

    @property
    def lead(self):
        return self.mons[0]

    @property
    def can_fight(self):
        if len(self.mons) == 1:
            return False
        return any([Mon.unpack(g).hpc > 0 for g in self.mons[1:]])

    def switch(self, index1: int, index2: int, update_pos_values: bool = False):
        """Switches two mons based on their indices (starting at 0) in the mon list."""
        temp = self.mons[index1]
        self.mons[index1] = self.mons[index2]
        self.mons[index2] = temp
        if update_pos_values:
            self.update_pos_values()

    def update_mon(self, mon: Mon):
        if mon.team_position <= len(self.mons):
            self.mons[self.has_mon(mon.team_position, "pos") - 1] = mon.pack
        else:
            raise ValueError("No such mon found.")

    def keys(self, compressed: bool = True):
        return none_list([f"{g.name} :: {g.key(compressed)}" for g in self.unpacked_mons], "\n")
