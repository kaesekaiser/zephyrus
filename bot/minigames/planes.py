from math import sin, cos, asin, acos, pi, log10, floor, log, atan2, sqrt
from random import choices, choice
from minigames.planecities import *
from geopy.geocoders import Nominatim
from time import time
from pyquery import PyQuery
import re
rads = {"km": 6371, "mi": 3958.76}
url = "https://www.google.com/maps/d/u/0/edit?hl=en&mid=1aoVneqZxmbqLxZrznFPyYbpKlCGC4hbx"
cd_url = "https://www.timeanddate.com/countdown/vacation?iso={}&p0=179&msg={}&font=slab&csz=1#"
with open("storage/citycountries.txt", "r") as f:
    af = f.readlines()
citcoundat = {l.split("|")[0]: l.split("|")[1] for l in af}
cities = {}
countries = {}
starter_names = ["Meadowlark", "Nightingale", "Endeavor", "Aurora", "Spirit", "Falcon", "Albatross"]
permit = "".join([*[chr(g) for g in range(65, 91)], *[chr(g) for g in range(97, 123)], "1234567890_-"])
pattern = r"\[\[\[[0-9.,\-]+\].+?\\n,null,[0-9]+"
specific_patterns = {
    "name": r"(?<=\[\\\"name\\\",\[\\\")[a-zA-Z]+?(?=\\\")",
    "coords": r"(?<=\[\[\[)[0-9.,\-]+?(?=\])",
    "val": r"(?<=\[\\\"description\\\",\[\\\")[0-9]+?(?=\\\")",
    "no": r"[0-9]+$"
}


def readurl(s: str):
    return str(PyQuery(s, {'title': 'CSS', 'printable': 'yes'}, encoding="utf8"))


def greatcirc(p1: tuple, p2: tuple, unit="km"):
    """coordinates must be in radians"""
    if p1 == p2:
        return 0
    return round(rads[unit] * acos(sin(p1[0]) * sin(p2[0]) + cos(p1[0]) * cos(p2[0]) * cos(abs(p2[1]-p1[1]))), 2)


def gcp(p1: tuple, p2: tuple, prog: float):
    """Given PROG[0,1], returns the point PROG of the way along the great circle between P1 and P2."""
    p1, p2 = rad(p1), rad(p2)
    d = 2*asin(sqrt((sin((p1[0]-p2[0])/2))**2 + cos(p1[0])*cos(p2[0])*(sin((p1[1]-p2[1])/2))**2))
    a = sin((1 - prog) * d) / sin(d)
    b = sin(prog * d) / sin(d)
    x = a * cos(p1[0]) * cos(p1[1]) + b * cos(p2[0]) * cos(p2[1])
    y = a * cos(p1[0]) * sin(p1[1]) + b * cos(p2[0]) * sin(p2[1])
    z = a * sin(p1[0]) + b * sin(p2[0])
    return round(atan2(z, sqrt(x ** 2 + y ** 2)) * 180 / pi, 5), round(atan2(y, x) * 180 / pi, 5)


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
        return [rd(g) for g in n]
    return rd(n)


def robinson_x(x):  # found this works better than neville approximation
    return 1.0000025782957427 - 4.3272151850971580 * 10 ** -4 * x ** 1 + 8.5901022917429554 * 10 ** -5 * x ** 2 \
        - 1.3912368796075018 * 10 ** -5 * x ** 3 + 5.0268816690188926 * 10 ** -7 * x ** 4 \
        + 1.1274054880604926 * 10 ** -8 * x ** 5 - 1.3740373454703167 * 10 ** -9 * x ** 6 \
        + 3.8359516009612151 * 10 ** -11 * x ** 7 - 3.5407459411354098 * 10 ** -13 * x ** 8 \
        - 2.0721836379074974 * 10 ** -15 * x ** 9 + 4.1009713014767920 * 10 ** -17 * x ** 10 \
        + 1.1315710050175688 * 10 ** -19 * x ** 11 + 3.5914393783068752 * 10 ** -21 * x ** 12 \
        - 1.7417023065426016 * 10 ** -22 * x ** 13 + 1.2711476309117433 * 10 ** -24 * x ** 14 \
        + 5.4153586840702526 * 10 ** -27 * x ** 15 - 9.3580564924063361 * 10 ** -29 * x ** 16 \
        + 2.8235077456069639 * 10 ** -31 * x ** 17


def neville(datax, datay, x):
    """
    Finds an interpolated value using Neville's algorithm.
    Input
      datax: input x's in a list of size n
      datay: input y's in a list of size n
      x: the x value used for interpolation
    Output
      p[0]: the polynomial of degree n
    """
    n = len(datax)
    p = n*[0]
    for k in range(n):
        for i in range(n-k):
            if k == 0:
                p[i] = datay[i]
            else:
                p[i] = ((x-datax[i+k])*p[i] + (datax[i]-x)*p[i+1]) / (datax[i]-datax[i+k])
    return p[0]


def robinson_y(x):
    rob_x = list(range(0, 95, 5))
    rob_y = [0, 0.062, 0.124, 0.186, 0.248, 0.31, 0.372, 0.434, 0.4958, 0.5571, 0.6176, 0.6769, 0.7346, 0.7903, 0.8435,
             0.8936, 0.9394, 0.9761, 1]
    return neville(rob_x, rob_y, x)


def rewritecits():
    with open("storage/citycountries.txt", "w") as ff:
        for i in citcoundat:
            ff.write("{}|{}|\n".format(i, citcoundat[i]))


class City:
    def __init__(self, name: str, coords: iter, val: int, no=0):
        self.name = name
        self.coords = coords
        self.radcoords = tuple(rad(c) for c in coords)
        self.imageCoords = {
            g: [
                1376 * g + round(0.8487 * 515 * g * robinson_x(abs(self.coords[0])) * rad(self.coords[1] - 10)),
                698 * g - round(1.3523 * 515 * g * robinson_y(abs(self.coords[0]))) * (-1 if self.coords[0] < 0 else 1)
            ] for g in [1, 2, 4]  # levels of magnification
        }
        self.passengers = val
        self.value = round((lambda n: 70 * n ** 0.37)(val))
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
        self.dict = {"Coordinates": f"({twodig(self.coords[0])}, {twodig(self.coords[1])})",
                     "Country": coun, "Annual Passengers": suff(val),
                     "Value": "Ȼ{}".format(addcomm(self.value))}
        self.jobs = []
        self.job_reset = 0
        if self.name.lower() not in cities:
            cities[self.name.lower()] = self

    @staticmethod
    def from_html(html: str):
        return City(
            re.search(specific_patterns["name"], html)[0],
            [float(g) for g in re.search(specific_patterns["coords"], html)[0].split(",")],
            int(re.search(specific_patterns["val"], html)[0]),
            int(re.search(specific_patterns["no"], html)[0])
        )

    def __eq__(self, other):
        return isinstance(other, City) and self.name == other.name

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

    @staticmethod
    def from_str(s: str):
        j = s.split("-")
        return Path(int(j[1]), code_city(j[0][:2]), *[code_city(g) for g in snip(j[0][2:], 2)])

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
        self.cities = sorted(cits, key=lambda c: c.value, reverse=True)
        if self.name.lower() not in countries:
            countries[self.name.lower()] = self

    @property
    def worth(self):
        return round(0.03 * sum([i.value for i in self.cities]))

    @staticmethod
    def from_name_only(name: str):
        """Requires that all cities have already been created."""
        return Country(name, [g for g in cities.values() if g.country.lower() == name.lower()])


class Plane:
    def __init__(self, model: Model, name: str, path: Path, jobs: list, upgrades: list):
        self._model = model
        self.upgrades = upgrades
        self.name = name
        self.path = path
        self.jobs = jobs

    @property
    def range(self):
        return round(self.fuel_cap / self.fuel_use * self.airspeed)

    @property
    def lpk(self):
        return round(self.fuel_use / self.airspeed, 2)

    @property
    def model(self):
        return self._model.name

    @property
    def airspeed(self):
        return self._model.airspeed * (1 + self.upgrades[0] * 0.25)

    @property
    def pass_cap(self):
        return self._model.cap

    @property
    def fuel_use(self):
        return self._model.fph * (1 + self.upgrades[0] * 0.25)

    @property
    def fuel_cap(self):
        return self._model.tank * (1 + self.upgrades[1] * 0.25)

    @staticmethod
    def from_str(s: str):
        j = s.split("^")
        return Plane(craft[j[1].lower()], j[0], Path.from_str(j[3]), snip(j[4], 5), [int(c) for c in j[2].split("/")])

    @staticmethod
    def new(model: str, name: str = ""):
        return Plane(craft[model], name, Path(0, cities["london"]), [], [0, 0])

    def __str__(self):
        return f"{self.name}^{self.model}^{'/'.join([str(g) for g in self.upgrades])}^{self.path}^{''.join(self.jobs)}"

    def __eq__(self, other):
        return str(self) == str(other)

    @property
    def fleet_str(self):
        loc = f"Location: {self.path[0].name}" if len(self.path) == 0 else \
            f"En-route: {self.path[1].name}\nETA: {hrmin(self.arrival - time())}"
        return f"Model: {self.model}\n{loc}"

    @property
    def dict(self):
        loc = {"Location": self.path[0].name} if len(self.path) == 0 else \
            {"En-route": "→".join([g.name for g in self.path.path]), "ETA": hrmin(self.arrival - time())}
        job = [f"``{g}`` [{code_city(g[2:4]).name} Ȼ{Job.from_str(g).pay}]" for g in self.jobs]
        return {"Model": self.model, **loc, "Available Slots": self.pass_cap - len(self.jobs),
                "Jobs": ", ".join(job) if len(self.jobs) > 0 else "none"}

    @property
    def stats(self):
        power_up = "" if not self.upgrades[0] else f" (+{25 * self.upgrades[0]}%)"
        tank_up = "" if not self.upgrades[1] else f" (+{25 * self.upgrades[1]}%)"
        return {
            "Airspeed": f"{round(self.airspeed)} km/hr{power_up}",
            "Fuel Usage": f"{round(self.fuel_use)} L/hr{power_up}",
            "Fuel Tank": f"{round(self.fuel_cap)} L{tank_up}",
            "Range": f"{self.range} km{tank_up}",
            "Power Level": self.upgrades[0], "Tank Level": self.upgrades[1]
        }

    @property
    def landed_at(self):
        return None if len(self.path) > 0 else self.path[0]

    @property
    def is_full(self):
        return len(self.jobs) == self.pass_cap

    def load(self, job: str):
        if self.is_full:
            raise ValueError("fully loaded")
        self.jobs.append(job.upper())

    def unload(self, job: str):
        self.jobs.remove(job)

    def launch(self, *dests: City):
        self.path = Path(int(time()), self.path[0], *dests)

    def travel(self, fro: City, to: City):  # travel time
        return round(fro.dist(to) * 60 / self.airspeed)

    @property
    def arrival(self):
        return self.path.time + sum([self.travel(self.path[g - 1], self.path[g]) for g in range(1, len(self.path) + 1)])

    @property
    def next_eta(self):
        if len(self.path) == 0:
            return 0
        return self.path.time + self.travel(self.path[0], self.path[1])


class Job:  # tbh kind of a dummy class. doesn't really do anything other than serve as a convenience
    def __init__(self, fro: City, to: City):
        self.source = fro
        self.destination = to
        self.code = f"{self.source.code}{self.destination.code}"
        self.pay = round((self.source.dist(self.destination) / 4) ** 1.2)

    @staticmethod
    def from_str(s: str):
        return Job(code_city(s[:2]), code_city(s[2:4]))

    def __str__(self):
        return self.code

    def __eq__(self, other):
        return type(other) == Job and self.source.name == other.source.name and \
               self.destination.name == other.destination.name


class User:
    def __init__(self, no: int, licenses: list, cits: list, pns: dict, creds: float):
        self.id = no
        self.countries = licenses
        self.cities = cits
        self.planes = pns
        self.credits = creds

    @staticmethod
    def from_str(s: str):
        j = s.split("|")  # id|countries|cities|planes|credits
        p = [Plane.from_str(g) for g in j[3].split("~")]
        c = [code_city(g).name for g in j[2].split("~")]
        k = [backCountries[g] for g in j[1].split("~")]
        return User(int(j[0]), k, c, {g.name.lower(): g for g in p}, int(j[4]))

    def __str__(self):
        return f"{self.id}|{'~'.join([planemojis[g] for g in self.countries])}|" \
               f"{'~'.join([cities[g.lower()].code for g in self.cities])}|" \
               f"{'~'.join([str(g) for g in self.planes.values()])}|{round(self.credits)}"

    @property
    def jobs(self):
        return [g for item in self.planes.values() for g in item.jobs]

    def rename(self, old_name: str, new_name: str):
        self.planes[new_name.lower()] = self.planes[old_name.lower()]
        del self.planes[old_name.lower()]
        self.planes[new_name.lower()].name = new_name


def find_city(s: str):
    return cities[c_alias.get(s.lower(), s.lower())]


def from_flag(s: str):  # gets country code from regional indicators
    if False not in [ord(g) in range(127462, 127488) for g in s]:
        return "".join(chr(ord(g) - 127365) for g in s)
    return s


def find_country(s: str):
    return countries[k_alias.get(s.lower(), backCountries.get(from_flag(s.lower()), s.lower())).lower()]


def code_city(s: str):
    try:
        ret = list(cities.values())[int(s, 36)]
        assert isinstance(ret, City)
        return ret
    except IndexError:
        raise ValueError("invalid city code")


def priority(a1: City, a2: City, lis=False):
    if a1.dist(a2) <= log10(a1.passengers) * 25:
        return -100
    ff = lambda x: (-1 / 3 * x ** -3 + 4 / 3 * (x - 1) ** 3 + 4 / 3) ** 1.5
    airport_factor = log10(a1.passengers) - 2
    destination_factor = log10(a2.passengers) - 2
    domestic_factor = (7.5 - airport_factor) / 2 if a1.country == a2.country else 0
    dist_factor = a1.dist(a2) / 1000
    dist_factor = 20 - dist_factor * ff(4 / airport_factor)
    if lis:
        return [destination_factor, dist_factor, domestic_factor]
    return max(destination_factor + dist_factor + domestic_factor, 0)


k_alias = {
    "uk": "unitedkingdom", "greatbritain": "unitedkingdom", "britain": "unitedkingdom", "usa": "unitedstates",
    "america": "unitedstates", "uae": "unitedarabemirates", "car": "centralafricanrepublic", "dprk": "northkorea",
    "png": "papuanewguinea", "drc": "drcongo", "czechrepublic": "czechia", "arabia": "saudiarabia", "persia": "iran",
    "burma": "myanmar", "republicofcongo": "congo", "republicofthecongo": "congo", "fyrom": "macedonia",
    "papua": "papuanewguinea", "eswatini": "swaziland", "newguinea": "papuanewguinea", "dr": "dominicanrepublic",
    "northmacedonia": "macedonia",
}
c_alias = {
    "ny": "newyork", "nyc": "newyork", "mexico": "mexicocity", "guatemalacity": "guatemala", "juarez": "ciudadjuarez",
    "panama": "panamacity", "kuwaitcity": "kuwait", "luxemburg": "luxembourg", "brunei": "bandarseribegawan",
    "bsb": "bandarseribegawan", "jfk": "newyork", "lax": "losangeles", "atl": "atlanta", "rdu": "raleigh",
    "newyorkcity": "newyork", "charlestonsc": "charlestonsouthcarolina", "compostela": "santiagodecompostela",
    "charlestonwv": "charlestonwestvirginia", "la": "losangeles", "delhi": "newdelhi", "bombay": "mumbai"
}
emojiCountries = {
    "ac": "Ascension Island", "ad": "Andorra", "ae": "United Arab Emirates", "af": "Afghanistan",
    "ag": "Antigua and Barbuda", "ai": "Anguilla", "al": "Albania", "am": "Armenia", "ao": "Angola", "aq": "Antarctica",
    "ar": "Argentina", "as": "American Samoa", "at": "Austria", "au": "Australia", "aw": "Aruba", "ax": "Åland Islands",
    "az": "Azerbaijan", "ba": "Bosnia and Herzegovina", "bb": "Barbados", "bd": "Bangladesh", "be": "Belgium",
    "bf": "Burkina Faso", "bg": "Bulgaria", "bh": "Bahrain", "bi": "Burundi", "bj": "Benin", "bl": "St. Barthélemy",
    "bm": "Bermuda", "bn": "Brunei", "bo": "Bolivia", "bq": "Caribbean Netherlands", "br": "Brazil", "bs": "Bahamas",
    "bt": "Bhutan", "bv": "Bouvet Island", "bw": "Botswana", "by": "Belarus", "bz": "Belize", "ca": "Canada",
    "cc": "Cocos Islands", "cd": "Congo-Kinshasa", "cf": "Central African Republic", "cg": "Congo-Brazzaville",
    "ch": "Switzerland", "ci": "Côte d'Ivoire", "ck": "Cook Islands", "cl": "Chile", "cm": "Cameroon", "cn": "China",
    "co": "Colombia", "cp": "Clipperton Island", "cr": "Costa Rica", "cu": "Cuba", "cv": "Cape Verde", "cw": "Curaçao",
    "cx": "Christmas Island", "cy": "Cyprus", "cz": "Czechia", "de": "Germany", "dg": "Diego Garcia", "dj": "Djibouti",
    "dk": "Denmark", "dm": "Dominica", "do": "Dominican Republic", "dz": "Algeria", "ea": "Ceuta and Melilla",
    "ec": "Ecuador", "ee": "Estonia", "eg": "Egypt", "eh": "Western Sahara", "er": "Eritrea", "es": "Spain",
    "et": "Ethiopia", "eu": "European Union", "fi": "Finland", "fj": "Fiji", "fk": "Falkland Islands",
    "fm": "Micronesia", "fo": "Faroe Islands", "fr": "France", "ga": "Gabon", "gb": "United Kingdom", "gd": "Grenada",
    "ge": "Georgia", "gf": "French Guiana", "gg": "Guernsey", "gh": "Ghana", "gi": "Gibraltar", "gl": "Greenland",
    "gm": "Gambia", "gn": "Guinea", "gp": "Guadeloupe", "gq": "Equatorial Guinea", "gr": "Greece",
    "gs": "South Georgia and South Sandwich Islands", "gt": "Guatemala", "gu": "Guam", "gw": "Guinea-Bissau",
    "gy": "Guyana", "hk": "Hong Kong", "hm": "Heard and McDonald Islands", "hn": "Honduras", "hr": "Croatia",
    "ht": "Haiti", "hu": "Hungary", "ic": "Canary Islands", "id": "Indonesia", "ie": "Ireland", "il": "Israel",
    "im": "Isle of Man", "in": "India", "io": "British Indian Ocean Territory", "iq": "Iraq", "ir": "Iran",
    "is": "Iceland", "it": "Italy", "je": "Jersey", "jm": "Jamaica", "jo": "Jordan", "jp": "Japan", "ke": "Kenya",
    "kg": "Kyrgyzstan", "kh": "Cambodia", "ki": "Kiribati", "km": "Comoros", "kn": "St. Kitts and Nevis",
    "kp": "North Korea", "kr": "South Korea", "kw": "Kuwait", "ky": "Cayman Islands", "kz": "Kazakhstan", "la": "Laos",
    "lb": "Lebanon", "lc": "St. Lucia", "li": "Liechtenstein", "lk": "Sri Lanka", "lr": "Liberia", "ls": "Lesotho",
    "lt": "Lithuania", "lu": "Luxembourg", "lv": "Latvia", "ly": "Libya", "ma": "Morocco", "mc": "Monaco",
    "md": "Moldova", "me": "Montenegro", "mf": "Saint Martin", "mg": "Madagascar", "mh": "Marshall Islands",
    "mk": "Macedonia", "ml": "Mali", "mm": "Myanmar", "mn": "Mongolia", "mo": "Macau", "mp": "Northern Mariana Islands",
    "mq": "Martinique", "mr": "Mauritania", "ms": "Montserrat", "mt": "Malta", "mu": "Mauritius", "mv": "Maldives",
    "mw": "Malawi", "mx": "Mexico", "my": "Malaysia", "mz": "Mozambique", "na": "Namibia", "nc": "New Caledonia",
    "ne": "Niger", "nf": "Norfolk Island", "ng": "Nigeria", "ni": "Nicaragua", "nl": "Netherlands", "no": "Norway",
    "np": "Nepal", "nr": "Nauru", "nu": "Niue", "nz": "New Zealand", "om": "Oman", "pa": "Panama", "pe": "Peru",
    "pf": "French Polynesia", "pg": "Papua New Guinea", "ph": "Philippines", "pk": "Pakistan", "pl": "Poland",
    "pm": "St. Pierre and Miquelon", "pn": "Pitcairn Islands", "pr": "Puerto Rico", "ps": "Palestine", "pt": "Portugal",
    "pw": "Palau", "py": "Paraguay", "qa": "Qatar", "re": "Réunion", "ro": "Romania", "rs": "Serbia", "ru": "Russia",
    "rw": "Rwanda", "sa": "Saudi Arabia", "sb": "Solomon Islands", "sc": "Seychelles", "sd": "Sudan", "se": "Sweden",
    "sg": "Singapore", "sh": "St. Helena", "si": "Slovenia", "sj": "Svalbard and Jan Mayen", "sk": "Slovakia",
    "sl": "Sierra Leone", "sm": "San Marino", "sn": "Senegal", "so": "Somalia", "sr": "Suriname", "ss": "South Sudan",
    "st": "São Tomé and Príncipe", "sv": "El Salvador", "sx": "Sint Maarten", "sy": "Syria", "sz": "Swaziland",
    "ta": "Tristan da Cunha", "td": "Chad", "tf": "French Southern Territories", "tg": "Togo", "th": "Thailand",
    "tj": "Tajikistan", "tk": "Tokelau", "tl": "Timor-Leste", "tm": "Turkmenistan", "tn": "Tunisia", "to": "Tonga",
    "tr": "Turkey", "tt": "Trinidad and Tobago", "tv": "Tuvalu", "tw": "Taiwan", "tz": "Tanzania", "ua": "Ukraine",
    "ug": "Uganda", "um": "U.S. Outlying Islands", "un": "United Nations", "us": "United States", "uy": "Uruguay",
    "uz": "Uzbekistan", "va": "Vatican City", "vc": "St. Vincent and Grenadines", "ve": "Venezuela",
    "vg": "British Virgin Islands", "vi": "U.S. Virgin Islands", "vn": "Vietnam", "vu": "Vanuatu",
    "wf": "Wallis and Futuna", "ws": "Samoa", "xk": "Kosovo", "ye": "Yemen", "yt": "Mayotte", "za": "South Africa",
    "zm": "Zambia", "zw": "Zimbabwe"
}
specialCases = {
    "TimorLeste": "tl", "GuineaBissau": "gw", "IvoryCoast": "ci", "Bosnia": "ba", "DRCongo": "cd",  "Congo": "cg",
    "SaoTome": "st", "USVirginIslands": "vi", "Curacao": "cw", "StLucia": "lc", "StKittsandNevis": "kn",
    "StVincent": "vc"
}
planemojis = {**{"".join(emojiCountries[g].split()): g for g in emojiCountries}, **specialCases}
backCountries = {j: g for g, j in planemojis.items()}
