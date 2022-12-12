from discord.ext.commands import CommandError
from typing import Union
Flint = Union[float, int]


def unit_list_to_string(l: list, negative: bool = False):
    exponent_order = sorted(list(set(l)), key=lambda c: [l.count(c), ord(c[0])])
    return "∙".join(
        f"{g}^{'-' if negative else ''}{l.count(g)}" if (l.count(g) > 1 or negative) else g for g in exponent_order
    )


class MultiUnit:
    def __init__(self, top_units: list = tuple(), bottom_units: list = tuple()):
        self.topUnits = list(top_units)
        self.bottomUnits = list(bottom_units)
        self.cancel_out()

    def cancel_out(self):
        for i in self.topUnits.copy():
            if i in self.bottomUnits:
                self.topUnits.remove(i)
                self.bottomUnits.remove(i)

    @property
    def units_contained(self):
        return set(self.topUnits).union(set(self.bottomUnits))

    @property
    def valid_units(self):
        return all([u in j for u in self.units_contained for g in conversionTable for j in g.systems])

    @property
    def directly_derived(self):
        """bool: Whether or not the unit is defined directly in terms of the SI base units."""
        return all({g in derived_units for g in self.units_contained})

    @property
    def is_simple(self):
        return any([self.base_terms_of() == g.base_terms_of() for g in derived_units.values()])

    def base_metric(self):
        """NOTE: this only works for units defined wholly and directly in terms of the BASE UNITS."""
        if not self.directly_derived:
            raise ValueError("base_metric() can only be used for units defined directly in terms of the base units.")

        ret = MultiUnit.null()
        for unit in self.topUnits:
            base_unit = [g for g in conversionTable if unit in g.systems[0]][0].baseUnit
            ret *= base_unit.eq
        for unit in self.bottomUnits:
            base_unit = [g for g in conversionTable if unit in g.systems[0]][0].baseUnit
            ret /= base_unit.eq

        ret.cancel_out()
        return ret

    def base_terms_of(self):
        """NOTE: this does NOT preserve changes in the value of the measurement. ONLY use for checking if two units are
        convertible. For metric units, use base_metric()."""
        ret = MultiUnit.null()

        for unit in self.topUnits:
            base_unit = [g.baseUnit for g in conversionTable for j in g.systems if unit in j][0]
            ret *= base_unit.eq

        for unit in self.bottomUnits:
            base_unit = [g.baseUnit for g in conversionTable for j in g.systems if unit in j][0]
            ret /= base_unit.eq

        ret.cancel_out()
        return ret

    def convertible(self, other):
        assert isinstance(other, MultiUnit)
        return self.base_terms_of() == other.base_terms_of()

    @staticmethod
    def null():
        return MultiUnit([], [])

    @staticmethod
    def from_str(s: str, force_units: bool = False):
        if s.count("/") > 1:
            raise ValueError("Too many slashes. Please only use one slash - for example, instead of m/s/s, use m/s^2.")

        def is_neg_exp(u: str):
            return "^" in u and int(u.split("^")[1]) < 0

        def single_unit(u: str):
            if "^" in u:
                return [u.split("^")[0] if force_units else find_abbr(u.split("^")[0])] * abs(int(u.split("^")[1]))
            else:
                return [u if force_units else find_abbr(u)]

        first_split = [g.split("*") if g else [] for g in (s.split("/") if "/" in s else [s, ""])]
        ret = [[], []]

        for i in [0, 1]:
            for unit in first_split[i]:
                if unit == "1":
                    continue
                try:
                    int(unit.split("^")[1])
                except ValueError:
                    raise CommandError("Power must be an integer.")
                except IndexError:
                    ret[i].extend(single_unit(unit))
                else:
                    if is_neg_exp(unit):
                        ret[not i].extend(single_unit(unit))
                    else:
                        ret[i].extend(single_unit(unit))

        return MultiUnit(*ret)

    def __bool__(self):
        return bool(self.topUnits) or bool(self.bottomUnits)

    def __eq__(self, other):
        if not isinstance(other, MultiUnit):
            return False
        return sorted(self.topUnits) == sorted(other.topUnits) and sorted(self.bottomUnits) == sorted(other.bottomUnits)

    def __str__(self):
        if self.topUnits:
            if self.bottomUnits:
                return unit_list_to_string(self.topUnits) + "/" + unit_list_to_string(self.bottomUnits)
            else:
                return unit_list_to_string(self.topUnits)
        else:
            return unit_list_to_string(self.bottomUnits, negative=True)

    def __mul__(self, other):
        assert isinstance(other, MultiUnit), f"Cannot multiply a MultiUnit by an object of class {type(other)}."
        return MultiUnit(self.topUnits + other.topUnits, self.bottomUnits + other.bottomUnits)

    def __truediv__(self, other):
        assert isinstance(other, MultiUnit), f"Cannot divide a MultiUnit by an object of class {type(other)}."
        return MultiUnit(self.topUnits + other.bottomUnits, self.bottomUnits + other.topUnits)


def metric_dict(unit: str, factor: Flint = None):
    met = {"Y": 1e24, "Z": 1e21, "E": 1e18, "P": 1e15, "T": 1e12, "G": 1e9, "M": 1e6,
           "k": 1000, "h": 100, "da": 10, "": 1, "d": 0.1, "c": 0.01, "m": 0.001,
           "μ": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15, "a": 1e-18, "z": 1e-21, "y": 1e-24}
    return {g + unit: ((j * factor) if factor else j) for g, j in met.items()}


def metric_name_dict(unit: str, abbreviation: str):
    met = {"yotta": "Y", "zetta": "Z", "exa": "E", "peta": "P", "tera": "T", "giga": "G", "mega": "M", "kilo": "k",
           "hecto": "h", "deca": "da", "deka": "da", "": "", "deci": "d", "centi": "c", "milli": "m", "micro": "μ",
           "nano": "n", "pico": "p", "femto": "f", "atto": "a", "zepto": "z", "yocto": "y"}
    return {f"u{abbreviation}": f"μ{abbreviation}", f"mc{abbreviation}": f"μ{abbreviation}",
            **{g + unit: j + abbreviation for g, j in met.items()}}


def narahl_dict(unit: str):  # using the Narahl metric-ish system
    nar = {"noma": 24 ** 6, "sira": 24 ** 4, "nila": 24 ** 3, "benna": 576, "dara": 24, "": 1,
           "dika": 1/24, "rani": 1/576, "juna": 1/24 ** 3, "caya": 1/24 ** 4, "hana": 1/24 ** 6}
    return {g + unit: j for g, j in nar.items()}


def add_degree(s: str):
    return s if s == "K" else "°" + s


class BaseUnit:
    def __init__(self, val: str, eq: str):
        """val: the fancy unit; eq: the equivalent value in SI base units"""
        self.val = MultiUnit.from_str(val, True)
        self.eq = MultiUnit.from_str(eq, True)


def convert_multi(n: Flint, fro: MultiUnit, to: MultiUnit = None):
    if str(to) == "base":
        to = fro.base_terms_of()

    if to == fro:
        return str(to), n

    if not to:
        if str(fro) not in flattenedConvTable:
            raise CommandError("For combinations of multiple units, please include a unit to convert to.")
        else:
            cg = [g for g in conversionTable for j in g.systems if str(fro) in j][0]
            if str(fro) in cg.systems[0] and (len(cg.systems) == 1 or not cg.systems[1]):
                raise CommandError(
                    f"There's no imperial alternative to `{str(fro)}`." +
                    ("\n`z!conv` reads `C` as coulombs. If you wanted Celsius, use `z!tconv`." if str(fro) == "C" else
                     "\n`z!conv` reads `F` as farads. If you wanted Fahrenheit, use `z!tconv`." if str(fro) == "F" else
                     "")
                )
            else:
                try:
                    # this converts index 0 (metric) to index 1 (imperial) and vice versa
                    to_dict = cg.systems[str(fro) in cg.systems[0]]
                except IndexError:
                    raise CommandError("There's no alternative system to convert to.")
                possible = {g: cg.convert(n, str(fro), g) for g in to_dict if g in defaultUnits}
                possible = dict(sorted(possible.items(), key=lambda g: max(g[1] / 3, 3 / g[1])))
                return list(possible)[0], possible[list(possible)[0]]

    if not fro.convertible(to):
        raise CommandError("Units are not equal.")

    # convert both to base SI units
    n_mul, n_div = 1, 1
    if not fro.directly_derived:
        for unit in fro.topUnits:
            cg = [g for g in conversionTable for j in g.systems if unit in j][0]
            n_mul = cg.convert(n_mul, unit, str(cg.baseUnit.val))
        for unit in fro.bottomUnits:
            cg = [g for g in conversionTable for j in g.systems if unit in j][0]
            n_div = cg.convert(n_div, unit, str(cg.baseUnit.val))

    if not to.directly_derived:
        for unit in to.topUnits:
            cg = [g for g in conversionTable for j in g.systems if unit in j][0]
            n_div = cg.convert(n_div, unit, str(cg.baseUnit.val))
        for unit in to.bottomUnits:
            cg = [g for g in conversionTable for j in g.systems if unit in j][0]
            n_mul = cg.convert(n_mul, unit, str(cg.baseUnit.val))

    # and just like that
    return str(to), n * n_mul / n_div


class ConversionGroup:
    def __init__(self, *systems: dict, base_unit: BaseUnit, **inters: tuple):
        self.systems = systems
        self.allUnits = {j for g in systems for j in g}
        self.inters = inters
        self.baseUnit = base_unit  # baseUnit format: non-base unit, conversion factor, base unit
        for key, value in self.inters.items():
            [g for g in self.systems if key in g][0]["converter"] = key
            self.systems[0]["converter"] = value[1]

    def convert(self, n: Flint, fro: str, to: str):  # assumes both fro and to are in group
        if to == fro:
            return n
        fro_dict = [g for g in self.systems if fro in g][0]
        if to in fro_dict:
            return self.cws(n, fro, to, [g for g in self.systems if fro in g][0])
        to_dict = [g for g in self.systems if to in g][0]
        return self.cws(  # step 3: convert from system converter to desired unit
            self.cbs(  # step 2: convert between systems
                self.cws(  # step 1: convert to system converter
                    n, fro, fro_dict["converter"], fro_dict
                ), fro_dict["converter"], to_dict["converter"]
            ), to_dict["converter"], to, to_dict
        )

    def cbs(self, n: Flint, fro: str, to: str):  # convert between systems. uses metric as midpoint
        if to in self.systems[0]:
            return n * self.inters[fro][0]
        if fro in self.systems[0]:
            return n / self.inters[to][0]
        return self.cbs(self.cbs(n, fro, self.systems[0]["converter"]), self.systems[0]["converter"], to)

    @staticmethod
    def cws(n: Flint, fro: str, to: str, dic: dict):  # convert within system
        if dic[to] == dic[fro]:
            return n
        return n * dic[fro] / dic[to]


def temp_convert(n: Flint, fro: str, to: str = None):
    if not to:
        return temp_convert(n, fro, list(tempTable)[not list(tempTable).index(fro)])  # C to F; all else to C
    return to, tempTable[fro].get(to, lambda x: x)(n)


def find_abbr(s: str, temperature: bool = False):
    abb = tempAbbreviations if temperature else unitAbbreviations
    tab = tempTable if temperature else flattenedConvTable
    s = "".join(s.split("."))
    if s[-1] == "s" and s[:-1].lower() in abb:
        return abb[s[:-1].lower()]
    if s in tab:
        return s
    if s.lower() in abb:
        return abb[s.lower()]
    if "°" in s and not temperature:
        raise CommandError("Use `z!tconv` for temperature conversions.")
    raise CommandError(f"Invalid unit `{s}`.")


unitAbbreviations = {  # full name: abbreviation

    # length
    **metric_name_dict("meter", "m"),
    **metric_name_dict("metre", "m"),
    "inch": "in", "inches": "in", "foot": "ft", "feet": "ft", "yard": "yd", "mile": "mi", "fathom": "ftm",
    "astronomical unit": "AU",
    "linhardts": "linhardt",

    # mass
    **metric_name_dict("gram", "g"),
    **metric_name_dict("gramme", "g"),
    "ounce": "oz", "pound": "lb", "stone": "st", "hundredweight": "cwt", "short ton": "ton", "tons": "ton",
    "tonne": "Mg", "metric ton": "Mg",
    "atomic mass unit": "amu",
    **metric_name_dict("dalton", "Da"),

    # time
    **metric_name_dict("second", "s"),
    "minute": "min", "hour": "hr", "day": "d", "week": "wk", "h": "hr",
    **metric_name_dict("year", "yr"),

    # current
    **metric_name_dict("ampere", "A"),
    **metric_name_dict("amp", "A"),

    # area
    "hectare": "ha", "decare": "daa", "are": "a", "deciare": "da", "centiare": "ca",
    "acre": "ac",

    # volume
    **metric_name_dict("liter", "L"),
    **metric_name_dict("litre", "l"),
    "teaspoon": "tsp", "tablespoon": "tbsp", "fluid ounce": "fl oz", "cup": "c", "pint": "pt", "quart": "qt",
    "gallon": "gal", "barrel": "bbl",

    # frequency
    **metric_name_dict("hertz", "Hz"),

    # force
    **metric_name_dict("newton", "N"),
    "pound-force": "lbf",

    # pressure
    **metric_name_dict("pascal", "Pa"),
    **metric_name_dict("bar", "bar"),
    "PSI": "psi", "PSF": "psf", "atmosphere": "atm", "mmHg": "mm Hg", "inHg": "in Hg",

    # energy
    **metric_name_dict("joule", "J"),
    **metric_name_dict("electronvolt", "eV"),
    **metric_name_dict("electron-volt", "eV"),

    # power
    **metric_name_dict("watt", "W"),

    # charge
    **metric_name_dict("coulomb", "C"),

    # electric potential
    **metric_name_dict("volt", "V"),

    # capacitance
    **metric_name_dict("farad", "F"),

    # resistance
    **metric_name_dict("ohm", "Ω"),

    # electrical conductance
    **metric_name_dict("siemens", "S"),

    # magnetic flux
    **metric_name_dict("weber", "Wb"),

    # magnetic flux density
    **metric_name_dict("tesla", "T"),

    # inductance
    **metric_name_dict("henry", "H"),

    # base
    "base": "base"
}
unrulyAbbreviations = {  # abbreviations for whole complex units that might show up
    "mph": "mi/hr", "kph": "km/hr", "pound-foot": "lb*ft", "kmh": "km/hr"
}
tempAbbreviations = {
    "°C": "C", "celsius": "C", "centigrade": "C",
    "°F": "F", "fahrenheit": "F",
    "kelvin": "K",
    "°R": "R", "rankine": "R",
}


conversionTable = (  # groups of units of the same system

    # BASE UNITS
    ConversionGroup(  # length
        metric_dict("m"),
        {"in": 1, "ft": 12, "yd": 36, "mi": 12 * 5280, "ftm": 6 * 12},
        {"au": 1, "AU": 1, "ua": 1},
        {**narahl_dict("dari"), "cera": 576*8},
        {"linhardt": 1},
        **{"in": (0.0254, "m"), "au": (149597870700, "m"), "dari": (0.2056, "m"), "linhardt": (1.77, "m")},
        base_unit=BaseUnit("m", "m")
    ),
    ConversionGroup(  # mass
        metric_dict("g"),
        {"oz": 1, "lb": 16, "st": 16 * 14, "cwt": 1600, "ton": 32000, "long ton": 16 * 2240, "slug": 16 * 32.174},
        {"amu": 1, "u": 1, **metric_dict("Da")},
        lb=(453.59237, "g"),
        amu=(1.660539040 * 10 ** -24, "g"),
        base_unit=BaseUnit("kg", "kg")
    ),
    ConversionGroup(  # time
        {**metric_dict("s"), **metric_dict("sec"), "min": 60, "hr": 3600, "d": 86400, "wk": 86400 * 7,
         **metric_dict("yr", 31536000)},
        base_unit=BaseUnit("s", "s")
    ),
    ConversionGroup(  # current
        metric_dict("A"),
        base_unit=BaseUnit("A", "A")
    ),

    # DERIVED UNITS
    ConversionGroup(  # area
        {"ca": 1, "da": 10, "a": 100, "daa": 1000, "ha": 10000},
        {"ac": 1},
        ac=(0.40468564224, "ha"),
        base_unit=BaseUnit("ca", "m^2")
    ),
    ConversionGroup(  # volume
        {**metric_dict("L"), **metric_dict("l")},
        {"tsp": 1, "tbsp": 3, "fl oz": 6, "c": 48, "pt": 96, "qt": 192, "gal": 768,
         "bbl": 768 * 31.5, "hogshead": 768 * 63},
        tsp=(4.92892159375, "mL"),
        base_unit=BaseUnit("kL", "m^3")
    ),
    ConversionGroup(  # frequency
        metric_dict("Hz"),
        base_unit=BaseUnit("Hz", "s^-1")
    ),
    ConversionGroup(  # force
        metric_dict("N"),
        {"lbf": 1},
        lbf=(4.448222, "N"),
        base_unit=BaseUnit("N", "kg*m/s^2")
    ),
    ConversionGroup(  # pressure
        {**metric_dict("Pa"), **metric_dict("bar", 100000)},
        {"psi": 1, "psf": 144},
        {"atm": 1, "torr": 1/760},
        {"mm Hg": 1, "in Hg": 25.4},
        base_unit=BaseUnit("Pa", "kg/m*s^2"),
        **{"psi": (8896443230521/1290320000, "Pa"), "atm": (101325, "Pa"), "mm Hg": (133.322387, "Pa")}  # bc space
    ),
    ConversionGroup(  # energy (also torque)
        metric_dict("J"),
        {},  # this empty dict prevents [ z!conv 1 J ] from returning anything, since there's no imperial joule
        metric_dict("eV"),
        eV=(1.602176634e-19, "J"),
        base_unit=BaseUnit("J", "kg*m^2/s^2")
    ),
    ConversionGroup(  # power
        metric_dict("W"),
        base_unit=BaseUnit("W", "kg*m^2/s^3")
    ),
    ConversionGroup(  # charge
        metric_dict("C"),
        {},  # same as above; allows [ z!conv 1 e ] but not [ z!conv 1 C ]
        {"e": 1},
        e=(1.602176634e-19, "C"),
        base_unit=BaseUnit("C", "A*s")
    ),
    ConversionGroup(  # electric potential
        metric_dict("V"),
        base_unit=BaseUnit("V", "kg*m^2/A*s^3")
    ),
    ConversionGroup(  # capacitance
        metric_dict("F"),
        base_unit=BaseUnit("F", "s^4*A^2/kg*m^2")
    ),
    ConversionGroup(  # resistance
        metric_dict("Ω"),
        base_unit=BaseUnit("Ω", "kg*m^2/A^2*s^3")
    ),
    ConversionGroup(  # electrical conductance
        metric_dict("S"),
        base_unit=BaseUnit("S", "A^2*s^3/kg*m^2")
    ),
    ConversionGroup(  # magnetic flux
        metric_dict("Wb"),
        base_unit=BaseUnit("Wb", "kg*m^2/A*s^2")
    ),
    ConversionGroup(  # magnetic flux density
        metric_dict("T"),
        base_unit=BaseUnit("T", "kg/A*s^2")
    ),
    ConversionGroup(  # inductance
        metric_dict("H"),
        base_unit=BaseUnit("H", "kg*m^2/A^2*s^2")
    )
)
tempTable = {
    "C": {
        "F": lambda n: 9 * n / 5 + 32,
        "K": lambda n: n + 273.15,
        "R": lambda n: 9 * (n + 273.15) / 5,
    },
    "F": {
        "C": lambda n: 5 * (n - 32) / 9,
        "K": lambda n: 5 * (n - 32) / 9 + 273.15,
        "R": lambda n: n + 9 * 273.15 / 5 - 32,
    },
    "K": {
        "C": lambda n: n - 273.15,
        "F": lambda n: 9 * (n - 273.15) / 5 + 32,
        "R": lambda n: 9 * n / 5,
    },
    "R": {
        "C": lambda n: 5 * n / 9 - 273.15,
        "F": lambda n: n - 9 * 273.15 / 5 + 32,
        "K": lambda n: 5 * n / 9,
    }
}
flattenedConvTable = [j for g in conversionTable for j in g.allUnits]
# derived_units contains all the directly derived SI units (J, but not kJ; m, but not ft)
derived_units = {str(j.baseUnit.val): j.baseUnit.val for j in conversionTable}


defaultUnits = [  # units it's okay to default to if user doesn't give unit to which to convert
    "mm", "cm", "m", "km", "in", "ft", "mi", "mg", "g", "kg", "oz", "lb", "mL", "L", "ML", "tsp", "tbsp", "fl oz",
    "c", "pt", "qt", "gal", "s", "min", "hr", "d", "yr", "N", "kN", "lbf", "J", "kJ", "Pa", "MPa", "psi"
]


if __name__ == "__main__":
    print(MultiUnit.from_str("c").base_terms_of())
