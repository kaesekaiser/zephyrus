from math import sin, cos, acos, pi, log10, floor, log
from random import choices, choice
from minigames.planecities import *
from html.parser import HTMLParser
from geopy.geocoders import Nominatim
from time import time
import urllib.request as req
rads = {"km": 6371, "mi": 3958.76}
url = "https://www.google.com/maps/d/u/0/edit?hl=en&mid=1aoVneqZxmbqLxZrznFPyYbpKlCGC4hbx"
cd_url = "https://www.timeanddate.com/countdown/vacation?iso={}&p0=179&msg={}&font=slab&csz=1#"
with open("storage/citycountries.txt", "r") as f:
    af = f.readlines()
citcoundat = {l.split("|")[0]: l.split("|")[1] for l in af}
cities = {}
countries = {}
users = {}
starter_names = ["Meadowlark", "Nightingale", "Endeavor", "Aurora", "Spirit", "Falcon", "Albatross"]
permit = "".join([*[chr(g) for g in range(65, 91)], *[chr(g) for g in range(97, 123)], "1234567890_-"])


def greatcirc(p1: tuple, p2: tuple, unit="km"):
    if p1 == p2:
        return 0
    return round(rads[unit] * acos(sin(p1[0]) * sin(p2[0]) + cos(p1[0]) * cos(p2[0]) * cos(abs(p2[1]-p1[1]))), 2)


def twodig(no):
    n = round(no, 2)
    return str(n) if len(str(n).split(".")[1]) > 1 else str(float(n)) + "0"


def hrmin(m):
    return "{} min {} s".format(round(m) // 60, round(m) % 60)


def addcomm(n):
    if type(n) == str:
        add = ("." + n.split(".")[1]) if len(n.split(".")) > 1 else ""
    else:
        add = ("." + str(float(n)).split(".")[1]) if n % 1 != 0 else ""
    if len(str(n).split(".")[0]) < 5:
        return str(n).split(".")[0] + add
    ret, fat = "", list(reversed([c for c in str(n).split(".")[0]]))
    for i in range(len(fat)):
        ret = fat[i] + ret
        if i % 3 == 2 and len(str(n).split(".")[0]) > i + 1:
            ret = "," + ret
    return ret + add


def suff(n):
    if n < 1000:
        return n
    sfs, digs = str(n)[:3], floor(log10(n) - 3)
    ret = sfs if digs % 3 == 2 else str(float(sfs) / 10) if digs % 3 == 1 else twodig(float(sfs) / 100)
    suf = ["K", "M", "B", "T", "Q"][int(digs // 3)]
    return "{} {}".format(ret, suf)


def base36(n: int):
    if n == 0:
        return "0"
    chars = {**{g: str(g) for g in range(10)}, **{g + 10: chr(g + 65) for g in range(26)}}
    return "".join(reversed([chars[(n % (36 ** (g + 1))) // (36 ** g)] for g in range(int(log(n, 36)) + 1)]))


def snip(s: str, n: int):  # guts a string into n-long segments
    ret, build = [], ""
    for m in range(len(s)):
        build += s[m]
        if (m + 1) % n == 0:
            ret.append(build)
            build = ""
    return ret if len(s) >= n else [s] if len(s) > 0 else []


def rad(n):
    def rd(no):
        return pi * no / 180
    if type(n) in [list, tuple]:
        return [rd(i) for i in n]
    return rd(n)


def readurl(url):
    return str(req.urlopen(url).read())


def rewritecits():
    with open("storage/citycountries.txt", "w") as f:
        for i in citcoundat:
            f.write("{}|{}|\n".format(i, citcoundat[i]))


class MapParser(HTMLParser):
    def __init__(self):
        self.printing = False
        self.json = ""
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag == "script" and ("type", "text/javascript") in attrs:
            self.printing = True

    def handle_data(self, data):
        if self.printing is True:
            self.json = data

    def handle_endtag(self, tag):
        if tag == "script":
            self.printing = False


class Map:
    def __init__(self, table):
        self.str = table.split("U.S. Regions")[0].split("null,null,null,null,0,2,null,")[1]\
                   .split("]\\\\n]\\\\n,[[[")[0][2:] + "]"
        self.table = []
        rank, dat = 0, ""
        for char in self.str:
            dat += char
            if char == "[":
                rank += 1
            if char == "]":
                rank -= 1
            if rank == 0:
                if len(dat) > 1:
                    self.table.append(dat)
                dat = ""
        self.cities = [c[c.find("\"name\\"):].split('\\\\\"')[2] for c in self.table]
        self.coords = [tuple(round(float(g), 5) for g in c[c.find("[[[")+3:].split("]")[0].split(","))
                       for c in self.table]
        self.descs = [c[c.find("\"description\\"):].split("\\\\\"")[2] for c in self.table]


class City:
    def __init__(self, name: str, coords: iter, val, no=0):
        self.name = name
        self.coords = coords
        self.radcoords = tuple(rad(c) for c in coords)
        self.passengers = int(val)
        self.worth = round((lambda n: 70 * n ** 0.37)(int(val)))
        self.no = no
        self.code = base36(self.no).rjust(2, "0")
        if self.name in citcoundat:
            coun = citcoundat[self.name]
        else:
            coun = Nominatim().reverse(self.coords).raw["address"]["country"]
            coun = countredirs.get(coun, coun)
            print(name, coun)
            citcoundat[self.name] = coun
            rewritecits()
        self.country = coun
        self.value = {"Coordinates": f"({twodig(self.coords[0])}, {twodig(self.coords[1])})",
                      "Country": coun, "Annual Passengers": suff(int(val)),
                      "Value": "Ȼ{}".format(addcomm(self.worth))}
        self.jobs = []
        self.job_reset = 0
        if self.name.lower() not in cities:
            cities[self.name.lower()] = self

    def __eq__(self, other):
        return self.name == other.name

    def dist(self, other):
        return greatcirc(self.radcoords, other.radcoords)

    def rpj(self):
        ds = choices(list(cities.values()), weights=[2 ** priority(self, g) for g in cities.values()],
                     k=round((log(self.passengers, 10) - 2.75) ** 2.5 * 1.5))
        self.jobs = sorted([Job(self, cities[g.name.lower()]) for g in ds],
                           key=lambda jb: jb.pay, reverse=True)
        for j in range(len(self.jobs)):
            self.jobs[j].code += \
                choice([chr(g) for g in range(65, 91) if chr(g) not in
                        [self.jobs[h].code[4] for h in range(j) if self.jobs[h].code[:4] == self.jobs[j].code[:4]]])


class Path:
    def __init__(self, start_time: int, start_city: City, *dests: City):
        self.time = start_time
        self.fro = start_city
        self.path = list(dests)

    def __str__(self):
        return f"{self.fro.code}{''.join([g.code for g in self.path])}-{self.time}"

    def __len__(self):
        return len(self.path)

    def __getitem__(self, item: int):
        if item == 0:
            return self.fro
        if item > 0:
            return self.path[item - 1]
        if item < 0:
            return self[len(self) + 1 + item]

    def __iter__(self):
        return [self.fro, *self.path]

    def iterate(self, travel: int):
        self.fro = self.path.pop(0)
        self.time = round(self.time + travel)

    def append(self, city: City):
        self.path.append(city)


class Country:
    def __init__(self, name: str, cits: list):
        self.name = name
        self.cities = sorted(cits, key=lambda c: c.worth, reverse=True)
        self.worth = round(0.03 * sum([i.worth for i in self.cities]))
        if self.name.lower() not in countries:
            countries[self.name.lower()] = self


class Plane:
    def __init__(self, model: Model, name: str, path: Path, jobs: list, upgrades: list):
        self.model = model.name
        self.airspeed = model.airspeed * (1 + upgrades[0] * 0.25)
        self.passcap = model.cap
        self.fueluse = model.fph * (1 + upgrades[0] * 0.25)
        self.fuelcap = model.tank * (1 + upgrades[1] * 0.25)
        self.upgrades = upgrades
        self.range = round(self.fuelcap / self.fueluse * self.airspeed)
        self.lpk = round(self.fueluse / self.airspeed, 2)
        self.name = name
        self.path = path
        self.jobs = jobs

    def __str__(self):
        return f"{self.name}^{self.model}^{''.join([str(g) for g in self.upgrades])}^{self.path}^{''.join(self.jobs)}"

    def __eq__(self, other):
        return str(self) == str(other)

    def fleet_str(self):
        loc = f"Location: {self.path[0].name}" if len(self.path) == 0 else \
            f"En-route: {self.path[1].name}\nETA: {hrmin(self.arrival() - time())}"
        return f"Model: {self.model}\n{loc}"

    def dict(self):
        loc = {"Location": self.path[0].name} if len(self.path) == 0 else \
            {"En-route": "→".join([g.name for g in self.path.path]), "ETA": hrmin(self.arrival() - time())}
        job = [f"``{g}`` [{code_city(g[2:4]).name} Ȼ{js(g).pay}]" for g in self.jobs]
        return {"Model": self.model, **loc, "Available Slots": self.passcap - len(self.jobs),
                "Jobs": ", ".join(job) if len(self.jobs) > 0 else "none"}

    def stats(self):
        return {"Airspeed": f"{round(self.airspeed)} km/hr", "Fuel Usage": f"{round(self.fueluse)} L/hr",
                "Fuel Tank": f"{round(self.fuelcap)} L", "Range": f"{self.range} km",
                "Power Level": self.upgrades[0], "Tank Level": self.upgrades[1]}

    def load(self, job: str):
        if len(self.jobs) == self.passcap:
            raise ValueError("fully loaded")
        self.jobs.append(job.upper())

    def unload(self, job: str):
        self.jobs.remove(job)

    def launch(self, *dests: City):
        self.path = Path(int(time()), self.path[0], *dests)

    def travel(self, fro: City, to: City):  # travel time
        return round(fro.dist(to) * 60 / self.airspeed)

    def arrival(self):
        return self.path.time + sum([self.travel(self.path[g - 1], self.path[g]) for g in range(1, len(self.path) + 1)])


def blank_plane(model: str):
    return Plane(craft[model], "", Path(0, cities["london"]), [], [0, 0])


class User:
    def __init__(self, no: str, licenses: list, cits: list, pns: dict, creds: float):
        self.no = no
        self.countries = licenses
        self.cities = cits
        self.planes = pns
        self.credits = creds
        if str(self.no) not in users:
            users[str(self.no)] = self

    def __str__(self):
        return f"{self.no}|{'~'.join(self.countries)}|{'~'.join(self.cities)}|" \
               f"{'~'.join([str(g) for g in self.planes.values()])}|{round(self.credits)}"

    def jobs(self):
        return [g for item in self.planes.values() for g in item.jobs]

    def rename(self, old_name: str, new_name: str):
        self.planes[new_name.lower()] = self.planes[old_name.lower()]
        del self.planes[old_name.lower()]
        self.planes[new_name.lower()].name = new_name


class Job:  # tbh kind of a dummy class. doesn't really do anything other than serve as a convenience
    def __init__(self, fro: City, to: City):
        self.source = fro
        self.destination = to
        self.code = f"{self.source.code}{self.destination.code}"
        self.pay = round((self.source.dist(self.destination) / 4) ** 1.2)

    def __str__(self):
        return self.code

    def __eq__(self, other):
        return type(other) == Job and self.source.name == other.source.name and \
               self.destination.name == other.destination.name


def ps(s: str):  # takes name^model^upgrades^path^jobs and returns Plane object
    j = s.split("^")
    return Plane(craft[j[1].lower()], j[0], hs(j[3]), snip(j[4], 5), [int(c) for c in j[2]])


def us(s: str, no: str=None):  # same as ps() but for User class
    j = s.split("|")  # id|countries|cities|planes|credits
    i = j[0] if no is None else no
    p = [ps(g) for g in j[3].split("~")]
    return User(i, j[1].split("~"), j[2].split("~"), {g.name.lower(): g for g in p}, int(j[4]))


def js(s: str):  # for jobs
    return Job(code_city(s[:2]), code_city(s[2:4]))


def hs(s: str):  # for paths
    j = s.split("-")
    return Path(int(j[1]), code_city(j[0][:2]), *[code_city(g) for g in snip(j[0][2:], 2)])


def find_city(s: str):
    return cities[c_alias.get(s.lower(), s.lower())]


def find_country(s: str):
    return countries[k_alias.get(s.lower(), s.lower())]


def code_city(s: str):
    try:
        return list(cities.values())[int(s, 36)]
    except IndexError:
        raise ValueError("invalid city code")


def priority(a1: City, a2: City, lis=False):
    if a1.dist(a2) <= log10(a1.passengers) * 25:
        return -100
    f = lambda x: (-1 / 3 * x ** -3 + 4 / 3 * (x - 1) ** 3 + 4 / 3) ** 1.5
    airport_factor = log10(a1.passengers) - 2
    destination_factor = log10(a2.passengers) - 2
    domestic_factor = (7.5 - airport_factor) / 2 if a1.value["Country"] == a2.value["Country"] else 0
    dist_factor = a1.dist(a2) / 1000
    dist_factor = 20 - dist_factor * f(4 / airport_factor)
    if lis:
        return [destination_factor, dist_factor, domestic_factor]
    return max(destination_factor + dist_factor + domestic_factor, 0)


k_alias = {"uk": "unitedkingdom", "greatbritain": "unitedkingdom", "britain": "unitedkingdom", "gb": "unitedkingdom",
           "us": "unitedstates", "usa": "unitedstates", "america": "unitedstates", "uae": "unitedarabemirates",
           "car": "centralafricanrepublic", "dprk": "northkorea", "png": "papuanewguinea", "drc": "drcongo",
           "czechrepublic": "czechia", "arabia": "saudiarabia", "persia": "iran", "burma": "myanmar",
           "nk": "northkorea", "sk": "southkorea", "sa": "southafrica", "republicofcongo": "congo",
           "republicofthecongo": "congo", "fyrom": "macedonia", "papua": "papuanewguinea",
           "newguinea": "papuanewguinea", "nz": "newzealand", "dr": "dominicanrepublic"}
c_alias = {"ny": "newyork", "nyc": "newyork", "mexico": "mexicocity", "guatemalacity": "guatemala",
           "panama": "panamacity", "kuwaitcity": "kuwait", "luxemburg": "luxembourg", "brunei": "bandarseribegawan",
           "bsb": "bandarseribegawan", "jfk": "newyork", "lax": "losangeles", "atl": "atlanta", "rdu": "raleigh",
           "newyorkcity": "newyork", "charlestonsc": "charlestonsouthcarolina", "compostela": "santiagodecompostela",
           "charlestonwv": "charlestonwestvirginia", "la": "losangeles", "delhi": "newdelhi", "bombay": "mumbai"}
