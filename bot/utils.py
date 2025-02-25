import asyncio
import datetime
import discord
import hanziconv
import random
import re
import requests
from classes.bot import Zeph
from classes.embeds import author_from_user, blue, choose, ClientEmol, construct_embed, Emol, lost, success, wiki
from classes.menus import Navigator, page_list
from discord.ext import commands
from functions import add_commas, can_int, hex_to_color, lower_alphabet, plural, smallcaps
from functools import partial
from math import atan2, ceil, floor, isclose, log, log10, pi, sqrt
from minigames.imaging import global_fill
from PIL import Image
from sympy import factorint
from unicodedata import name as uni_name
from urllib.error import HTTPError
from utilities.words import longest_common_subsequence

from utilities import dice as di, weed as wd, timein as ti, wiki as wk, convert as cv, keys as api_keys


def squarize(s: str, joiner="\u2060"):
    noms = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    return joiner.join([chr(127462 - 97 + ord(g.lower())) if ord(g.lower()) in range(97, 123) else
                        ":{}:".format(noms[int(g)]) if ord(g) in range(48, 58) else
                        ":question:" if g == "?" else ":exclamation:" if g == "!" else g for g in s])


def caesar_cipher(letter: str, n: int):
    if letter.lower() not in lower_alphabet:
        return letter
    if letter.isupper():
        return caesar_cipher(letter.lower(), n).upper()
    return lower_alphabet[(lower_alphabet.index(letter) + n) % 26]


def vig(letter: str, *keys: str, reverse: bool = False):
    if letter.lower() not in lower_alphabet:
        return letter
    if letter.isupper():
        return vig(letter.lower(), *keys, reverse=reverse).upper()
    mul = -1 if reverse else 1
    return lower_alphabet[(lower_alphabet.index(letter) +
                           mul * sum([lower_alphabet.index(g.lower()) for g in keys])) % 26]


def gradient(from_hex: str, to_hex: str, value: float | int):
    from_value = 1 - value
    return hex_to_color(
        "".join([hex(int(int(from_hex[g:g+2], 16) * from_value + int(to_hex[g:g+2], 16) * value))[2:]
                 for g in range(0, 5, 2)])
    )


def apostrophe_feet_to_decimal(s: str) -> float:
    return int(s.split("'")[0]) + float(s.split("'")[1].strip("\"")) / 12


def modified_lcs(s1: str, query: str):
    # used for find_user and z!esearch

    if query.lower() == s1.lower():  # search identical to name
        return 0  # result = 0
    if query.lower() in s1.lower():  # name contains string, prioritizing shorter names + names that start with string
        return 0 + (len(s1) - len(query)) / 32 + (s1.lower().index(query.lower()) != 0)  # 0 < result < 2
    # sort remainder by longest common subsequence, shorter names first
    return 32 - longest_common_subsequence(s1.lower(), query.lower()) + len(s1) / 32 + 2  # result > 2


def find_user(guild: discord.Guild, s: str):
    # including a very slight bias towards actual username
    return sorted(guild.members, key=lambda c: min(modified_lcs(c.name, s), modified_lcs(c.display_name, s) + 0.01))[0]


emojiCountries = {  # :flag_():
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


def interpret_potential_emoji(bot: Zeph, emote: str):
    try:
        uni_name(emote)
    except TypeError:
        try:
            emote.split(":")[2]
        except IndexError:
            if emote == chr(int("1f3f3", 16)) + "\ufe0f\u200d" + chr(int("1f308", 16)):
                name = "gay"
            elif emote == chr(int("1f3f4", 16)) + "\u200d\u2620\ufe0f":
                name = "pirates"
            elif emote in ["".join([chr(ord(c) + 127365) for c in g]) for g in emojiCountries]:
                name = emojiCountries["".join([chr(ord(c) - 127365) for c in emote])].lower()
            elif re.search(r"[🏻🏼🏽🏾🏿‍♂♀]+", emote):
                name = interpret_potential_emoji(bot, "".join(re.split(r"[🏻🏼🏽🏾🏿‍♂♀]+", emote)))
            else:
                raise commands.CommandError("Only input one character.")
        else:
            if emote.split(":")[1] not in bot.all_emojis:
                raise commands.CommandError("I don't have access to that emote.")
            else:
                name = emote.split(":")[1]
    except ValueError:
        raise commands.CommandError("Invalid character.")
    else:
        name = uni_name(emote)
    return name


class WikiNavigator(Navigator):
    def __init__(self, bot: Zeph, *results: wk.Result):
        self.results = results
        super().__init__(bot, wiki, [g.desc for g in results], 1)

    def con(self):
        return self.emol.con(
            self.results[self.page - 1].title.replace("****", ""), footer=f"{self.page}/{self.pgs}",
            d=self.results[self.page - 1].desc.replace("****", ""),
            url=f"https://en.wikipedia.org{self.results[self.page - 1].link}"
        )


x_sampa_dict = {
    "d`z`": "ɖ͡ʐ", "t`s`": "ʈ͡ʂ", r"dK\\": "d͡ɮ", "tK": "t͡ɬ", r"dz\\": "d͡ʑ", r"ts\\": "t͡ɕ", "dz`": "d͡ʐ",
    "ts`": "t͡ʂ", "dz": "d͡z", "ts": "t͡s", "dZ": "d͡ʒ", "tS": "t͡ʃ",
    r'\|\\\|\\': 'ǁ', r'G\\_<': 'ʛ', r'J\\_<': 'ʄ', '_B_L': '᷅', '_H_T': '᷄', '_R_F': '᷈', 'b_<': 'ɓ', 'd_<': 'ɗ',
    'g_<': 'ɠ', r'r\\`': 'ɻ', '<F>': '↘', '<R>': '↗', r'_\?\\': 'ˤ', 'd`': 'ɖ', r'h\\': 'ɦ', r'j\\': 'ʝ', 'l`': 'ɭ',
    r'l\\': 'ɺ', 'n`': 'ɳ', r'p\\': 'ɸ', 'r`': 'ɽ', r'r\\': 'ɹ', 's`': 'ʂ', r's\\': 'ɕ', r't`': 'ʈ', r'v\\': 'ʋ',
    r'x\\': 'ɧ', 'z`': 'ʐ', r'z\\': 'ʑ', r'B\\': 'ʙ', r'G\\': 'ɢ', r'H\\': 'ʜ', r'I\\': 'ᵻ', r'J\\': 'ɟ',
    r'K\\': 'ɮ', r'L\\': 'ʟ', r'M\\': 'ɰ', r'N\\': 'ɴ', r'O\\': 'ʘ', r'R\\': 'ʀ', r'U\\': 'ᵿ', r'X\\': 'ħ',
    r'\?\\': 'ʕ', r':\\': 'ˑ', r'@\\': 'ɘ', r'3\\': 'ɞ', r'<\\': 'ʢ', r'>\\': 'ʡ', r'!\\': 'ǃ', r'\|\|': '‖',
    r'\|\\': 'ǀ', r'=\\': 'ǂ',
    r'-\\': '‿', '_"': '̈', r'_\+': '̟', '_-': '̠', '_/': '̌', r'_\\': '̂', '_0': '̥', '_>': 'ʼ', r'_\^': '̯',
    '_}': '̚', '_A': '̘', '_a': '̺', '_B': '̏', '_c': '̜', '_d': '̪', '_e': '̴', '_F': '̂', '_G': 'ˠ', '_H': '́',
    '_h': 'ʰ', '_j': 'ʲ', '_k': '̰', '_L': '̀', '_l': 'ˡ', '_M': '̄', '_m': '̻', '_N': '̼', '_n': 'ⁿ', '_O': '̹',
    '_o': '̞', '_q': '̙', '_R': '̌', '_r': '̝', '_T': '̋', '_t': '̤', '_v': '̬', '_w': 'ʷ', '_X': '̆', '_x': '̽',
    '_=': '̩', '_~': '̃',
    r'\{': 'æ', 'A': 'ɑ', 'B': 'β', 'C': 'ç', 'D': 'ð', 'E': 'ɛ', 'F': 'ɱ', 'G': 'ɣ', 'H': 'ɥ', 'I': 'ɪ', 'J': 'ɲ',
    'K': 'ɬ', 'L': 'ʎ', 'M': 'ɯ', 'N': 'ŋ', 'O': 'ɔ', 'P': 'ʋ', 'Q': 'ɒ', r'R': 'ʁ', 'S': 'ʃ', 'T': 'θ', 'U': 'ʊ',
    'V': 'ʌ', 'W': 'ʍ', 'X': 'χ', 'Y': 'ʏ', 'Z': 'ʒ', '"': 'ˈ', '%': 'ˌ', "'": 'ʲ', '’': 'ʲ', ':': 'ː', '@': 'ə',
    '}': 'ʉ', '1': 'ɨ', '2': 'ø', '3': 'ɜ', '4': 'ɾ', '5': 'ɫ', '6': 'ɐ', '7': 'ɤ', '8': 'ɵ', '9': 'œ', '&': 'ɶ',
    r'\|': '|', r'\^': 'ꜛ', '!': 'ꜜ', '=': '̩', '`': '˞', '~': '̃', r'\.': '.', r'\?': 'ʔ', r'\)': '͡', '0': '∅',
    '-': '', r'\*': ''
}
z_sampa_dict = {  # taken from the late conniebot
    'n_0_l_!': 'ᵑ̊ǁ', 'n`_0_!': 'ᵑ̊ǃ', 'm_0_!': 'ᵑ̊ʘ', 'n_0_!': 'ᵑ̊ǀ', 't_l_!': 'ǁ', 'd_l_!': 'ᶢǁ', 'n_l_!': 'ᵑǁ',
    'n_0_7': 'ᵑ̊ǁ', 'J_0_!': 'ᵑ̊ǂ', 'J_0_7': 'ᵑ̊ǂˡ', 'N_0_!': 'ᶰ̊ʞ', '|\\|\\': 'ǁ', 't`_!': 'ǃ', 'd`_!': 'ᶢǃ',
    'n`_!': 'ᵑǃ', 'J\\_!': 'ᶢǂ', 'J\\_7': 'ᶢǂˡ', 'd`_<': 'ᶑ', 'J\\_<': 'ʄ', 'G\\_<': 'ʛ', 't`_<': 'ƭ̢', 't`_m': 'ȶ',
    'd`_m': 'ȡ', 'n`_m': 'ȵ', 'l`_m': 'ȴ', 't`s`': 'ʈ͡ʂ', 'd`z`': 'ɖ͡ʐ', '+r\\`': 'ʵ', 'p_!': 'ʘ', 'b_!': 'ᶢʘ',
    'm_!': 'ᵑʘ', 't_!': 'ǀ', 'd_!': 'ᶢǀ', 'n_!': 'ᵑǀ', 't_7': 'ǁ', 'd_7': 'ᶢǁ', 'n_7': 'ᵑǁ', 'c_!': 'ǂ', 'J_!': 'ᵑǂ',
    'c_7': 'ǂˡ', 'J_7': 'ᵑǂˡ', 'k_!': 'ʞ', 'g_!': 'ʞ̬', 'N_!': 'ᶰʞ', 'b_<': 'ɓ', 'd_<': 'ɗ', 'g_<': 'ɠ', 'p_<': 'ƥ',
    't_<': 'ƭ', 'c_<': 'ƈ', 'k_<': 'ƙ', 'q_<': 'ʠ', 'ts\\': 't͡ɕ', 'dz\\': 'd͡ʑ', 'dK\\': 'd͡ɮ', 'k_p': 'k͡p',
    'g_b': 'g͡b', 'N_m': 'ŋ͡m', '_a\\': '̳', '_d\\': '͆', '_f\\': '͌', '_H\\': 'ꜝ', '_l\\': '͔', '_N\\': '̼̻',
    '_P\\': 'ᵝ', '_r\\': '͕', '_t\\': '̪͆', '_v)': '̬₎', '_V\\': '˯', '_W\\': 'ᶣ', '_0)': '̥₎', '_%\\': 'ʢ',
    '_=\\': '˭', '_?\\': 'ˁ', '_\\\\': '-\\\\', '_~\\': '͊', '+s\\': 'ᶝ', '+J\\': 'ᶡ', '+h\\': 'ʱ', '+i\\': 'ᶤ',
    '+I\\': 'ᶧ', '+j\\': 'ᶨ', '+l`': 'ᶩ', '+L\\': 'ᶫ', '+M\\': 'ᶭ', '+n`': 'ᶯ', '+N\\': 'ᶰ', '+p\\': 'ᶲ', '+p"': 'ᵖ',
    '+r\\': 'ʴ', '+s`': 'ᶳ', '+u\\': 'ᶶ', '+z`': 'ᶼ', '+z\\': 'ᶽ', '+?\\': 'ˤ', '_<\\': '↓', '_>\\': '↑', 'c\\`': 'ɽ͡r',
    'd\\`': 'ᴅ̢', 'K\\`': 'ɭ̝', 'l\\`': 'ɺ̢', 'r\\`': 'ɻ', '+v\\': 'ᶹ', '#\\`': 'ɖ̆', '-\\\\': '\\\\', 'O\\': 'ʘ',
    '=\\': 'ǀ', '!\\': 'ǃ', '|\\': 'ǂ', 'k\\': 'ʞ', 'ts': 't͡s', 'dz': 'd͡z', 'tS': 't͡ʃ', 'dZ': 'd͡ʒ', 'tK': 't͡ɬ',
    '_a': '̺', '_A': '̘', '_B': '̏', '_c': '̜', '_C': '͍', '_d': '̪', '_e': '̴', '_E': '̼', '_f': '͎', '_F': '̂',
    '_G': 'ˠ', '_h': 'ʰ', '_H': '́', '_j': 'ʲ', '_J': '̡', '_k': '̰', '_K': '̰', '_l': 'ˡ', '_L': '̀', '_m': '̻',
    '_M': '̄', '_n': 'ⁿ', '_N': '̼', '_o': '̞', '_O': '̹', '_P': '̪', '_q': '̙', '_r': '̝', '_R': '̌', '_T': '̋',
    '_t': '̤', '_v': '̬', '_w': 'ʷ', '_W': 'ᵝ', '_x': '̽', '_X': '̆', '_y': '͉', '_Y': '͈', '_0': '̥', '_7': 'ǁ',
    '_8': '̣', '_9': '͚',
    '_!': '!', '_"': '̈', '_+': '̟', '_-': '̠', '_/': '̌', '_;': '͋', '_=': '̩', '_?': 'ˀ', '_\\': '̂', '_^': '̯',
    '_}': '̚', '_`': '̢', '_~': '̃', '_(': '₍', '_)': '₎', '_1': '¹', '_2': '²', '_3': '³', '_4': '⁴', '_5': '⁵',
    '_6': '⁶', '+a': 'ᵃ', '+â': 'ᵄ', '+6': 'ᵄ', '+A': 'ᵅ', '+{': 'ᵆ', '+ä': 'ᵆ', '+æ': 'ᵆ', '+Å': 'ᶛ', '+Q': 'ᶛ',
    '+b': 'ᵇ', '+B': 'ᵝ', '+c': 'ᶜ', '+D': 'ᶞ', '+d': 'ᵈ', '+e': 'ᵉ', '+@': 'ᵊ', '+E': 'ᵋ', '+Ê': 'ᶟ', '+3': 'ᶟ',
    '+f': 'ᶠ', '+g': 'ᶢ', '+G': 'ˠ', '+h': 'ʰ', '+H': 'ᶣ', '+i': 'ⁱ', '+î': 'ᶤ', '+1': 'ᶤ', '+I': 'ᶦ', '+Î': 'ᶧ',
    '+j': 'ʲ', '+k': 'ᵏ', '+l': 'ˡ', '+m': 'ᵐ', '+F': 'ᶬ', '+n': 'ⁿ', '+J': 'ᶮ', '+N': 'ᵑ', '+o': 'ᵒ', '+O': 'ᵓ',
    '+ô': 'ᶱ', '+8': 'ᶱ', '+p': 'ᵖ', '+r': 'ʳ', '+R': 'ʶ', '+s': 'ˢ', '+S': 'ᶴ', '+t': 'ᵗ', '+T': 'ᶿ', '+u': 'ᵘ',
    '+ï': 'ᵚ', '+M': 'ᵚ', '+}': 'ᶶ', '+û': 'ᶶ', '+U': 'ᶷ', '+Ë': 'ᶺ', '+V': 'ᶺ', '+v': 'ᵛ', '+w': 'ʷ', '+x': 'ˣ',
    '+X': 'ᵡ', '+ü': 'ʸ', '+y': 'ʸ', '+z': 'ᶻ', '+Z': 'ᶾ', '++': '⁺', '+-': '⁻', '+=': '⁼', '+(': '⁽', '+)': '⁾',
    '+:': '˸', '+0': '̊', '+?': 'ˀ', '_>': 'ʼ', '_<': 'ʼ↓', '<\\': 'ʢ', '>\\': 'ʡ', 'a\\': 'ä', 'A\\': 'ɐ̠', 'b\\': 'ⱱ',
    'B\\': 'ʙ', 'c\\': 'ᶉ', 'C\\': '\uf267', 'd`': 'ɖ', 'd\\': 'ᴅ', 'D`': 'ɻ̝', 'D\\': 'ʓ', 'e\\': 'ʢ̞', 'E\\': 'e̽',
    'f\\': 'ʩ', 'F\\': 'Ɬ', 'g\\': '¡̆', 'G\\': 'ɢ', 'h\\': 'ɦ', 'H\\': 'ʜ', 'i\\': 'ɨ', 'I\\': 'ᵻ', 'j\\': 'ʝ',
    'J\\': 'ɟ', 'K`': 'ꞎ', 'K\\': 'ɮ', 'l`': 'ɭ', 'l\\': 'ɺ', 'L\\': 'ʟ', 'm\\': 'ɯ̽', 'M\\': 'ɰ', 'n`': 'ɳ',
    'N\\': 'ɴ', 'o\\': 'o̽', 'p\\': 'ɸ', 'P\\': 'β̞', 'q\\': 'Ɬ̠', 'Q\\': 'Ɬ̠̬', '+P': 'ᶹ', 'r\\': 'ɹ', 'r`': 'ɽ',
    'R\\': 'ʀ', 's`': 'ʂ', 's\\': 'ɕ', 'S\\': 'ʪ', 't`': 'ʈ', 't\\': 'ʭ', 'T`': 'ɻ̝̊', 'T\\': 'ʆ', 'u\\': 'ʉ',
    'U\\': 'ᵿ', 'v\\': 'ʋ', 'V\\': 'ʟ̝', 'W\\': 'ⱱ̟', 'w\\': 'ʬ', 'x\\': 'ɧ', 'X\\': 'ħ', 'y\\': 'ʁ̞', 'Y\\': 'ʟ̠',
    'z`': 'ʐ', 'z\\': 'ʑ', 'Z\\': 'ʫ', '%\\': 'я', '@`': 'ɚ', '@\\': 'ɘ', '2\\': 'ø̽', '3\\': 'ɞ', '3`': 'ɝ',
    '4\\': 'ɢ̆', '5\\': 'ꬸ', '6\\': 'ʎ̝', '7\\': 'ɤ̽', '8\\': 'ɥ̝̊', '9\\': 'ʡ̮', ':\\': 'ˑ', '?\\': 'ʕ', '^\\': 'ğ',
    '&\\': 'ɶ̈', '#\\': 'd̮', '*\\': '\\*', '$\\': 'ʀ̟', '-\\': '‿', '||': '‖', ';\\': 'ǃ͡¡', '+\\': '⦀', '=': '̩',
    '~': '̃', "'": 'ʲ', 'a': 'a', 'ä': 'æ', 'â': 'ɐ', 'å': 'ɶ', 'A': 'ɑ', 'Â': 'ä', 'Å': 'ɒ', 'b': 'b', 'B': 'β',
    'c': 'c', 'C': 'ç', 'd': 'd', 'D': 'ð', 'e': 'e', 'ë': 'ɤ', 'ê': 'ɘ', 'E': 'ɛ', 'Ë': 'ʌ', 'Ê': 'ɜ', 'f': 'f',
    'F': 'ɱ', 'g': 'ɡ', 'G': 'ɣ', 'h': 'h', 'H': 'ɥ', 'ï': 'ɯ', 'î': 'ɨ', 'i': 'i', 'Ï': 'ɯ̽', 'Î': 'ᵻ', 'I': 'ɪ',
    'j': 'j', 'J': 'ɲ', 'k': 'k', 'K': 'ɬ', 'l': 'l', 'L': 'ʎ', 'm': 'm', 'M': 'ɯ', 'ñ': 'ɲ', 'n': 'n', 'N': 'ŋ',
    'o': 'o', 'ö': 'ø', 'ô': 'ɵ', 'O': 'ɔ', 'Ö': 'œ', 'Ô': 'ɞ', 'p': 'p', 'P': 'ʋ', 'q': 'q', 'Q': 'ɒ', 'r': 'r',
    'R': 'ʁ', 's': 's', 'S': 'ʃ', 't': 't', 'T': 'θ', 'u': 'u', 'û': 'ʉ', 'ü': 'y', 'U': 'ʊ', 'Û': 'ᵿ', 'Ü': 'ʏ',
    'v': 'v', 'V': 'ʌ', 'W': 'ʍ', 'w': 'w', 'x': 'x', 'X': 'χ', 'y': 'y', 'Y': 'ʏ', 'z': 'z', 'Z': 'ʒ', '.': '.',
    '"': 'ˈ', ',': 'ˌ', '%': 'ˌ', '@': 'ə', '{': 'æ', '}': 'ʉ', '1': 'ɨ', '2': 'ø', '3': 'ɜ', '4': 'ɾ', '5': 'ɫ',
    '6': 'ɐ', '7': 'ɤ', '8': 'ɵ', '9': 'œ', '0': 'Ø', ':': 'ː', '?': 'ʔ', '^': 'ꜛ', '!': 'ꜜ', '&': 'ɶ', ')': '͡',
    '(': '͜', '-': '', '|': '|', '`': '˞', ';': '¡', '$': '͢'
}


def convert_x_sampa(s: str):
    ret = s
    for rep in x_sampa_dict:
        ret = re.sub(r"(?<!\*)" + rep, x_sampa_dict[rep], ret)
    return ret


def convert_z_sampa(s: str):
    ret = s

    # def convert_prefix(pf: str, match: re.Match):
    #     return z_sampa_prefixes[pf].format(match[0][:-len(pf.replace("\\(", "(").replace("\\\\", "\\"))])

    # for rep in z_sampa_prefixes:
    #     ret = re.sub("." + rep, lambda c: convert_prefix(rep, c), ret)

    def convert_tones(match: re.Match):
        tones = {"1": "˩", "2": "˨", "3": "˧", "4": "˦", "5": "˥", "F": "↘", "R": "↗"}
        return re.sub("[12345FR]", lambda c: tones[c[0]], match[0].strip("<>"))

    ret = re.sub("<[12345FR]+>", convert_tones, ret)

    for rep, sub in z_sampa_dict.items():
        ret = ret.replace(rep, sub)

    return ret


base_order = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def dec(n: str, from_base: int):
    for c in n:
        if c not in base_order[:from_base]:
            raise IndexError(f"invalid base {from_base} number {n}")
    n = "".join(list(reversed(n)))
    return sum([base_order.index(n[g]) * from_base ** g for g in range(len(n))])


def rebase(n: str | int, fro: int, to: int):
    n = dec(str(n), fro)
    if not n:
        return "0"
    return "".join(reversed([base_order[(n % (to ** (g + 1))) // (to ** g)] for g in range(int(log(n + 0.5, to)) + 1)]))


async def get_message_pointer(ctx: commands.Context, pointer: str, fallback=None, allow_fail: bool = False):
    """Tries to get a Message object from a pointer.
    If pointer is a string of carets, returns the Nth message back.
    If pointer is a valid link to or ID for a message, returns that message.
    If pointer is neither, returns the fallback input (default None).
    If allow_fail is True, a message not found error will not prevent execution."""

    mess = fallback
    if pointer == "^" * len(pointer):
        async for message in ctx.channel.history(before=ctx.message, limit=len(pointer)):
            mess = message  # really shoddy way to get the Nth message back. is there a better way? probably.
    else:
        try:
            mess = await commands.MessageConverter().convert(ctx, pointer)
        except commands.BadArgument as e:
            if not allow_fail:
                raise commands.CommandError(str(e))
    return mess


def name_focus(user: discord.User | discord.Member):
    return f"**{user.name}**#{user.discriminator}"


class RMNavigator(Navigator):
    def __init__(self, bot: Zeph, roles: list):
        super().__init__(
            bot, Emol(":clipboard:", hex_to_color("C1694F")), [name_focus(g) for g in roles[0].members],
            8, "Role Members [{page}/{pgs}]",
            prefix=f"Total: **{len(roles[0].members)}** ({roles[0].mention})\n\n"
        )
        self.roles = roles
        self.roleIndex = 0
        if len(roles) > 1:
            self.funcs["🔃"] = self.cycle_role

    @property
    def role(self):
        return self.roles[self.roleIndex]

    def cycle_role(self):
        self.roleIndex = (self.roleIndex + 1) % len(self.roles)
        self.table = [name_focus(g) for g in self.role.members]
        self.prefix = f"Total: **{len(self.role.members)}** ({self.role.mention})\n\n"
        self.page = 1


class Reminder:
    def __init__(self, author_id: int, text: str, timestamp: int):
        self.author = author_id
        self.text = text
        self.time = int(timestamp)

    def __str__(self):
        return f"{self.author}|{self.time}|{self.text}"

    def __eq__(self, other):
        return str(self) == str(other) and isinstance(other, Reminder)

    @staticmethod
    def from_str(s: str):
        return Reminder(int(s.split("|")[0]), "|".join(s.split("|")[2:]), round(float(s.split("|")[1])))


def load_reminders(bot: Zeph):
    bot.reminders.clear()
    with open("storage/reminders.txt", "r") as f:
        for rem in f.readlines():
            bot.reminders.append(Reminder.from_str(rem.strip("\n")))


def rgb_to_hsv(r: int, g: int, b: int):
    return round(atan2(sqrt(3) * (g - b), 2 * r - g - b) * 360 / (2 * pi)) % 360, \
           round(100 - 100 * min(r, g, b) / 255), \
           round(100 * max(r, g, b) / 255)


class RemindNavigator(Navigator):
    def __init__(self, bot: Zeph, user: discord.User):
        self.user = user
        rems = sorted([g for g in bot.reminders if g.author == self.user.id], key=lambda c: c.time)
        super().__init__(
            bot, Emol(":alarm_clock:", hex_to_color("DD2E44")), rems, 4, "Reminders [{page}/{pgs}]", timeout=180
        )
        self.funcs[self.bot.emojis["no"]] = self.close
        for g in range(self.per):
            self.funcs[f"remove {g+1}"] = partial(self.remove_reminder, g)
        self.funcs["remove all"] = self.remove_all

    @property
    def rems(self):
        return sorted([g for g in self.bot.reminders if g.author == self.user.id], key=lambda c: c.time)

    @property
    def pgs(self):
        return ceil(len(self.rems) / self.per)

    async def remove_reminder(self, n: int):
        try:
            rem = page_list(self.rems, self.per, self.page)[n]
        except IndexError:  # if there aren't that many listed on the page, do nothing
            return

        self.bot.reminders.remove(rem)
        await success.edit(self.message, "Reminder removed.")
        if len(self.rems) == 0:  # if you just removed your only reminder, close the menu
            self.closed_elsewhere = True
            await asyncio.sleep(2)
            return await self.close()
        else:
            if self.page > self.pgs:
                self.page -= 1
            return await asyncio.sleep(2)

    async def remove_all(self):
        for rem in list(self.rems):
            self.bot.reminders.remove(rem)
        await success.edit(self.message, "All reminders removed.")
        await asyncio.sleep(2)
        self.closed_elsewhere = True
        return await self.close()

    def con(self):
        return self.emol.con(
            self.title.format(page=self.page, pgs=self.pgs),
            d="\n".join(
                f"**`[{g+1}]`** {j.text} (<t:{j.time}:R>)"
                for g, j in enumerate(page_list(self.rems, self.per, self.page))
            ) + "\n\nTo remove a reminder, say `remove <#>` in chat, e.g. `remove 1`. "
                "You can also say `remove all` to get rid of all your reminders at once."
        )

    async def get_emoji(self, ctx: commands.Context):
        def pred(mr: discord.Message | discord.Reaction, u: discord.User):
            if isinstance(mr, discord.Message):
                return u == ctx.author and mr.channel == ctx.channel and mr.content in self.funcs.keys()
            else:
                return u == ctx.author and mr.message == self.message and mr.emoji in self.legal

        mess = (await self.bot.wait_for('reaction_or_message', timeout=self.timeout, check=pred))[0]

        if isinstance(mess, discord.Message):
            try:
                await mess.delete()
            except discord.HTTPException:
                pass
            return mess.content
        else:
            return mess.emoji

    async def close(self):
        if len(self.rems) == 0:
            await self.emol.edit(self.message, "Menu closed; you have no more reminders set.")
        else:
            await self.emol.edit(self.message, "This menu has closed.")
        await self.remove_buttons()


class CounterNavigator(Navigator):
    def __init__(self, bot: Zeph, start_at: int = 0, increment: int = 1):
        super().__init__(
            bot, Emol(":1234:", blue), per=increment, prev=bot.emojis["minus"], nxt=bot.emojis["plus"], timeout=300
        )
        self.page = start_at
        self.mode = "count"
        self.funcs[self.bot.emojis["settings"]] = self.change_mode

    async def change_mode(self):
        if self.mode == "count":
            self.mode = "settings"
        else:
            self.mode = "count"

    def con(self):
        if self.mode == "count":
            return self.emol.con(
                "Counter", d=f"**{add_commas(self.page)}**",
                footer="Use the buttons to count up or down."
            )
        else:
            return self.emol.con(
                "Settings",
                d="To change a setting, say `<option>:<value>` - for example, `increment:5`. You can "
                  "reset the counter via `value:0`.\n\n"
                  "`increment` must be an integer between 1 and 999,999,999.\n"
                  "`value` must be an integer between -999,999,999 and 999,999,999.\n"
                  "`title` must be less than 200 characters.",
                fs={"Increment by (`increment`)": add_commas(self.per),
                    "Current value (`value`)": add_commas(self.page),
                    "Title (`title`)": self.title},
                same_line=True
            )

    def advance_page(self, direction: int):
        if direction:
            self.page = round(self.page + self.per) if direction > 0 else round(self.page - self.per)

    @staticmethod
    def is_valid_setting(s: str):
        if s.count(":") != 1:
            return False

        option, value = s.lower().split(":")

        if option == "increment":
            return can_int(value) and len(value) < 10 and int(value) > 0
        elif option == "value":
            return can_int(value) and len(value.strip("-")) < 10
        elif option == "title":
            return len(value) <= 200
        else:
            return False

    def apply_settings_change(self, option: str, value: str):
        """Assumes that the string <option>:<value> passes is_valid_setting()."""

        if option.lower() == "increment":
            self.per = int(value)
        if option.lower() == "value":
            self.page = int(value)
        if option.lower() == "title":
            self.title = value

    async def get_emoji(self, ctx: commands.Context):
        if self.mode == "settings":
            def pred(mr: discord.Message | discord.Reaction, u: discord.User):
                if isinstance(mr, discord.Message):
                    return u == ctx.author and mr.channel == ctx.channel and self.is_valid_setting(mr.content)
                else:
                    return u == ctx.author and mr.emoji in list(self.funcs) and mr.message.id == self.message.id

            mess = (await self.bot.wait_for(
                'reaction_or_message', timeout=self.timeout, check=pred
            ))[0]
            if isinstance(mess, discord.Message):
                await mess.delete()
                self.apply_settings_change(*mess.content.split(":"))
                return "wait"
            elif isinstance(mess, discord.Reaction):
                return mess.emoji

        return (await self.bot.wait_for(
            'reaction_add', timeout=self.timeout, check=lambda r, u: r.emoji in self.legal and
            r.message.id == self.message.id and u == ctx.author
        ))[0].emoji


with open("utilities/stest.txt", "r") as fp:
    stest_sentences = fp.read().splitlines()


class UtilitiesCog(commands.Cog):
    def __init__(self, bot: Zeph):
        self.bot = bot

    @commands.command(
        usage="z!mock [text...]",
        description="DoEs ThIs To YoUr TeXt.",
        help="DoEs ThIs To YoUr TeXt. If no text is given, mocks the message above you.\n\n"
             "`guy: I think Zephyrus is bad\nperson: z!mock\nZephyrus: I tHiNk ZePhYrUs Is BaD`\n\n"
             "You can also reply to a message (using Discord's new reply feature) with `z!mock`, and it will mock "
             "that message."
    )
    async def mock(self, ctx: commands.Context, *input_text):
        def multi_count(s, chars):
            return sum([s.count(ch) for ch in chars])

        def dumb(s: str):
            return "".join(
                s[g].lower() if (g - multi_count(s[:g], (" ", "'", ".", "?", "!", "\""))) % 2 == s[0].isupper()
                else s[g].upper() for g in range(len(s))
            )

        text = " ".join(input_text)
        if not text:
            text = "^"  # use new message pointing system

        if ctx.message.reference:  # if the message is a reply to another message
            if input_text:
                raise commands.CommandError("Either reply to a message, OR manually input text. Don't do both.")

            ref = ctx.message.reference
            if ref.cached_message:  # check for the cached message first, it'll be faster
                text = ref.cached_message.content
            else:  # if not, try to manually fetch the referenced message
                try:
                    text = (await self.bot.get_channel(ref.channel_id).fetch_message(ref.message_id)).content
                except discord.HTTPException:
                    raise commands.CommandError("I couldn't find the referenced message, sorry.")

        elif await get_message_pointer(ctx, text, allow_fail=True):
            text = (await get_message_pointer(ctx, text)).content

        if not text:  # the ONLY reason this should be true is if the user has pointed to a message with no text
            raise commands.CommandError("That message has no text, so there's nothing to mock.")

        if not input_text:
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass

        return await ctx.send(dumb(text))

    @commands.command(
        usage="z!expand <text...>", hidden=True,
        help="D o e s \u00a0 t h i s \u00a0 t o \u00a0 y o u r \u00a0 t e x t ."
    )
    async def expand(self, ctx: commands.Context, *, text):
        return await ctx.send(" ".join([c for c in text]))

    @commands.command(
        aliases=["sq"], usage="z!square <text...>",
        help=squarize("Does this to your text.")
    )
    async def square(self, ctx: commands.Context, *, text):
        return await ctx.send(squarize(text))

    @commands.command(
        usage="z!clap <text...>\nz!clap",
        description="Does :clap: this :clap: to :clap: your :clap: text. :clap:",
        help="Does :clap: this :clap: to :clap: your :clap: text. :clap: "
             "If no text is given, claps the message above you."
    )
    async def clap(self, ctx: commands.Context, *, text: str = None):
        if not text:
            async for message in ctx.channel.history(limit=10):
                if message.id < ctx.message.id and message.content:
                    text = message.content
                    try:
                        await ctx.message.delete()
                    except discord.HTTPException:
                        pass
                    break

        return await ctx.send(" 👏 ".join(text.split()) + " 👏")

    @commands.command(
        usage="z!ping",
        help="Pong!"
    )
    async def ping(self, ctx: commands.Context):
        message = await ctx.send(":ping_pong:!")
        return await message.edit(
            content=f":ping_pong:! ({round((message.created_at - ctx.message.created_at).microseconds / 1000)} ms)")

    @commands.command(
        aliases=["dice"], usage="z!roll [dice]",
        description="Rolls some dice using standard dice notation.",
        help="Rolls some dice. Uses standard dice notation:\n`AdB` rolls `A` `B`-sided dice. `A` defaults to 1 "
             "if empty.\n`d%` becomes `d100`, and `dF` rolls Fudge dice, which are `[-1, -1, 0, 0, "
             "1, 1]`.\n`!` explodes a die if it rolls the highest number (that is, it rolls an additional extra "
             "die).\n`!>N`, `!<N`, `!=N` explodes a die if it's greater than, less than, or equal to `N`, "
             "respectively.\n`-H` drops the highest roll. `-L` drops the lowest.\n`+N` at the end of a die "
             "adds `N` to the total roll."
    )
    async def roll(self, ctx: commands.Context, die: str = "1d6"):
        dice = ClientEmol(":game_die:", hex_to_color("EA596E"), ctx)
        try:
            die = di.Die(die)
        except di.BadString as e:
            return await dice.say(str(e))
        else:
            return await dice.say(f"Rolling {die}...", d=die.run())

    @commands.command(
        name="smallcaps", aliases=["small"], usage="z!smallcaps <text...>",
        description=smallcaps("Does this to your text."),
        help=smallcaps("Does this to your text.") + " There is no small-caps X, and the small-caps F and S may not "
                                                    "display on some devices."
    )
    async def smallcaps_command(self, ctx: commands.Context, *, text: str):
        return await ctx.send(smallcaps(text))

    @commands.command(
        aliases=["rot"], usage="z!rot <shift #> <text...>",
        description="Puts text through a Caesar cipher.",
        help="Puts text through a Caesar cipher, which shifts all letters some number of positions down the alphabet."
             "\n\ne.g. `rot 5` shifts all letters down 5 positions, so `hello` becomes `mjqqt`. If you want to "
             "decipher a Caesar'd text, put in a negative shift number."
    )
    async def caesar(self, ctx: commands.Context, n: int, *, text: str):
        return await ctx.send("".join([caesar_cipher(c, n) for c in text]))

    @commands.command(
        aliases=["vig"], usage="z!vigenere <word> <keys...>",
        description="Puts text through a [Vigenere cipher](https://en.wikipedia.org/wiki/Vigen%C3%A8re_cipher).",
        help="Puts text through a [Vigenere cipher](https://en.wikipedia.org/wiki/Vigen%C3%A8re_cipher) using the "
             "provided keys. Note that the text can't contain any spaces, so use underscores or dashes if you want "
             "to space it."
    )
    async def vigenere(self, ctx: commands.Context, text: str, *keys: str):
        return await ctx.send("".join([vig(text[n], *(k[n % len(k)] for k in keys)) for n in range(len(text))]))

    @commands.command(
        aliases=["devig"], usage="z!devigenere <word> <keys...>",
        description="Deciphers Vigenere'd text.",
        help="Deciphers Vigenere'd text using the provided keys. Using a different set of keys than the text "
             "was encoded with, will more than likely return a garbled mess.\n\n"
             "`z!vig zephyrus bot` → `asiimkvg`\n`z!devig asiimkvg bot` → `zephyrus`\n"
             "`z!devig asiimkvg fun` → `vyvdsxqm`"
    )
    async def devigenere(self, ctx: commands.Context, text: str, *keys: str):
        return await ctx.send("".join(
            [vig(text[n], *(k[n % len(k)] for k in keys), reverse=True) for n in range(len(text))]
        ))

    @commands.command(
        usage="z!scramble <text...>",
        help="eDso thsi ot uryo xtt.e"
    )
    async def scramble(self, ctx: commands.Context, *, text: str):
        return await ctx.send(content=" ".join(["".join(random.sample(g, len(g))) for g in text.split()]))

    @commands.command(
        name="tconvert", hidden=True,
        aliases=["tc", "tconv"], usage="z!tconvert <temperature> <unit> to <unit>\nz!tconvert <temperature> <unit>",
        description="Converts between units of temperature.",
        help="Converts between units of temperature: C, F, K, and R. More info at "
             "https://github.com/kaesekaiser/zephyrus/blob/master/docs/convert.md."
    )
    async def tconvert_command(self, ctx: commands.Context, n: str, *text):
        if re.fullmatch(r"-?[0-9.°]+[A-Za-z]+", n):
            text = [re.search(r"[A-Za-z]+", n)[0], *text]
            n = re.match(r"-?[0-9.]+", n)[0]

        if "." in n:
            digits_in = len(n.split(".")[1])
        else:
            digits_in = 0
        n = float(n)

        if not text:
            raise commands.BadArgument

        if "to" in text:
            text = [cv.find_abbr(g, True) for g in " ".join(text).upper().split(" TO ")]
        else:
            text = (cv.find_abbr(" ".join(text).upper(), True), )

        try:
            ret = cv.temp_convert(n, *text)
        except ValueError:
            raise commands.CommandError(f"Can't convert between {text[0]} and {text[1]}.")
        else:
            if cv.temp_convert(n, text[0], "K")[1] < 0:
                raise commands.CommandError(f"{n} °{text[0]} is below absolute zero.")
            value = max(min(cv.temp_convert(n, text[0], "F")[1], 120), 0) / 120
            temp = ClientEmol(":thermometer:", gradient("88C9F9", "DD2E44", value), ctx)
            return await temp.say(f"{round(ret[1], digits_in) if digits_in else round(ret[1])} {cv.add_degree(ret[0])}",
                                  d=f"= {n} {cv.add_degree(text[0])}")

    @commands.command(
        name="convert", aliases=["c", "conv"],
        usage="z!convert <number> <unit...> to <unit...>\nz!convert <number> <unit...>",
        description="Converts between non-temperature units of measurement.",
        help="Converts between units of measurement. More info at "
             "https://github.com/kaesekaiser/zephyrus/blob/master/docs/convert.md."
    )
    async def convert_command(self, ctx: commands.Context, *, text):
        conv = ClientEmol(":straight_ruler:", hex_to_color("efc700"), ctx)

        if not text:
            raise commands.BadArgument

        user_input = text.split()[0]
        text = text.split()[1:]

        if re.fullmatch(r"-?[0-9.]+[A-Za-z]+", user_input):
            text = [re.search(r"[A-Za-z]+", user_input)[0], *text]
            user_input = re.match(r"-?[0-9.]+", user_input)[0]

        if not text:
            try:
                apostrophe_feet_to_decimal(user_input)
            except (ValueError, IndexError):
                raise commands.BadArgument

        elif text[0].lower().strip("°") in ("c", "f", "k", "r"):
            if len(text) == 1:
                return await self.tconvert_command(ctx, user_input, text[0])
            elif text[-1].lower().strip("°") in ("c", "f", "k", "r"):
                return await self.tconvert_command(ctx, user_input, text[0], "to", text[-1])

        # determining number of sig figs
        if "/" in user_input:  # fractional input
            try:
                digits_in = ceil(log10(float(user_input.split("/")[1])))
                n = float(user_input.split("/")[0]) / float(user_input.split("/")[1])
            except (ValueError, IndexError):
                raise commands.CommandError("Bad fractional input.")
        elif "'" in user_input:  # 5'11" type feet + inches input
            try:
                n = apostrophe_feet_to_decimal(user_input)
                digits_in = len("".join(user_input.split("'")[1].split(".")[1:])) + len(user_input.split("'")[0]) + 2
                if "to" in text and text[0] != "to":
                    raise commands.CommandError("When using abbreviated ft/in input, don't specify the unit separately.")
                text = ["ft", *text]
            except (ValueError, IndexError):
                raise commands.BadArgument
        else:
            if "e" in user_input:
                # number of digits provided to scientific notation
                digits_in = len("".join(user_input.split("e")[0].split(".")))
            elif "." in user_input:
                first_significant = [g for g in range(len(user_input)) if user_input[g] not in "-+0."][0]
                digits_in = len("".join(user_input[first_significant:].split(".")))  # number of significant figures
            else:
                digits_in = len(user_input)  # if it's just an integer
            digits_in = max(digits_in, 3)  # at least 3 sig figs no matter what

            try:
                n = float(user_input)
            except ValueError:
                raise commands.BadArgument

        if n < 0:
            n = -n

        round_in = (digits_in - floor(log10(n)) - 1) if (digits_in - floor(log10(n)) - 1) > 0 else 0

        if "to" in text:
            text = tuple(cv.MultiUnit.from_str(cv.unrulyAbbreviations.get(g, g)) for g in " ".join(text).split(" to "))
            if len(text) != 2:
                raise commands.BadArgument
        else:
            text = (cv.MultiUnit.from_str(cv.unrulyAbbreviations.get(" ".join(text), " ".join(text))), )

        ret = cv.convert_multi(n, *text)

        if ret[0] == "ft":
            digits_out = digits_in - floor(log10(ret[1])) - 2
            inc = round(12 * (ret[1] % 1), digits_out)
            if isclose(inc, int(inc), abs_tol=1e-10) and digits_out == 1:
                inc = round(inc)
            return await conv.say(f"{add_commas(floor(ret[1]))} ft {inc} in",
                                  d=f"= {round(n, round_in)} {text[0]}")

        if ret[1] == int(ret[1]):
            digits_out = -1
        else:
            digits_out = digits_in - floor(log10(ret[1])) - 1

        return await conv.say(f"{add_commas(round(ret[1], digits_out) if digits_out > 0 else round(ret[1]))} {ret[0]}",
                              d=f"= {round(n, round_in)} {text[0]}")

    @commands.command(
        aliases=["weed"], usage="z!sayno",
        help="Say no to drugs."
    )
    async def sayno(self, ctx: commands.Context):
        return await ClientEmol(":leaves:", hex_to_color("98e27c"), ctx).say(wd.sayno())

    @commands.command(
        aliases=["pick"], usage="z!choose <option...> or <option...> ...",
        help="Chooses one from a list of options."
    )
    async def choose(self, ctx: commands.Context, *, text: str):
        picks = re.split(r"\s+or\s+", text)
        string = random.choice(["I pick {}!", "Obviously it's {}.", "{}, of course.", "{}, obviously.", "Definitely {}."])
        return await choose.send(ctx, string.format(f"**{random.choice(picks)}**"))

    @commands.command(  # an easter egg command. z!choose but in a pidgin conlang.
        hidden=True, usage="z!tekat <option...> sing <option...> ...",
        help="Chooses one from a list of options, but in Lam Kiraga."
    )
    async def tekat(self, ctx: commands.Context, *, text: str):
        picks = re.split(r"\s+sing\s+", text)
        string = random.choice(["De tekat {}!"])  # will add more later
        return await choose.send(ctx, string.format(f"**{random.choice(picks)}**"))

    @commands.command(
        name="8ball", usage="z!8ball <question...>",
        help="The divine magic 8-ball answers your yes-or-no questions."
    )
    async def eightball(self, ctx: commands.Context, *, text: str):
        if not text:
            raise commands.MissingRequiredArgument

        options = ["It is certain.", "As I see it, yes.", "Reply hazy, try again.", "Don't count on it.",
                   "It is decidedly so.", "Most likely.", "Ask again later.", "My reply is no.",
                   "Without a doubt.", "Outlook good.", "Better not tell you now.", "My sources say no.",
                   "Yes - definitely.", "Yes.", "Cannot predict now.", "Outlook not so good.",
                   "You may rely on it.", "Signs point to yes.", "Concentrate and ask again.", "Very doubtful."]
        return await choose.send(ctx, random.choice(options))

    @commands.command(
        aliases=["colour"], usage="z!color <hex code>\nz!color <red> <green> <blue>\nz!color random",
        description="Shows you a color.",
        help="Returns the color that corresponds to your input. `random` will randomly generate a color."
    )
    async def color(self, ctx: commands.Context, *, col: str):
        if col.casefold() == "random".casefold():
            ret = discord.Colour.from_rgb(random.randrange(256), random.randrange(256), random.randrange(256))
        else:
            try:
                if len(col.split()) == 3:
                    ret = discord.Colour.from_rgb(*[int(g) for g in col.split()])
                else:
                    ret = hex_to_color(col.strip("#"))
            except ValueError:
                raise commands.CommandError(f"Invalid color {col}.")
        if not 0 <= ret.value <= 16777215:
            raise commands.CommandError(f"Invalid color {col}.")
        emol = ClientEmol(self.bot.emojis["color_wheel"], ret, ctx)
        global_fill(Image.open("images/color.png"), (255, 255, 255), ret.to_rgb())\
            .save(f"images/{str(ret.r)[-1]}{str(ret.b)[-1]}.png")
        image = await self.bot.image_url(f"images/{str(ret.r)[-1]}{str(ret.b)[-1]}.png")
        return await emol.say(f"#{hex(ret.value)[2:].rjust(6, '0')}", thumb=image,
                              d=f"**RGB:** {ret.to_rgb()}\n**HSV:** {rgb_to_hsv(*ret.to_rgb())}")

    @commands.command(
        usage="z!timein <place...>", aliases=["time", "ti"],
        description="Tells you what time it is somewhere.",
        help="Returns the current local time in `<place>`."
    )
    async def timein(self, ctx: commands.Context, *, place: str):
        try:
            ret = ti.format_time_dict(ti.time_in(place), False)
        except IndexError:
            raise commands.CommandError("Location not found.")
        except KeyError:
            raise commands.CommandError("Location too vague.")

        address = ti.placename(place)
        emoji = ret.split()[0]
        emoji = f":clock{(int(emoji.split(':')[0]) + (1 if int(emoji.split(':')[1]) >= 45 else 0) - 1) % 12 + 1}" \
                f"{'30' if 15 <= int(emoji.split(':')[1]) < 45 else ''}:"
        return await ClientEmol(emoji, hex_to_color("b527e5"), ctx).say(ret, footer=address)

    @commands.command(
        aliases=["simp"], usage="z!simplified <Traditional Chinese text...>",
        help="Converts Traditional Chinese characters to Simplified Chinese."
    )
    async def simplified(self, ctx: commands.Context, *, trad: str):
        return await ctx.send(hanziconv.HanziConv.toSimplified(trad))

    @commands.command(
        aliases=["trad"], usage="z!traditional <Simplified Chinese text...>",
        help="Converts Simplified Chinese characters to Traditional Chinese."
    )
    async def traditional(self, ctx: commands.Context, *, simp: str):
        return await ctx.send(hanziconv.HanziConv.toTraditional(simp))

    @commands.command(
        aliases=["avi", "pfp"], usage="z!avatar [user]",
        description="Returns a link to a user's avatar.",
        help="Returns a link to a user's avatar. If `[user]` is left blank, links your avatar.\n\n"
             "This command works slightly differently in DMs. When used in a server, `[user]` will be converted to a "
             "member of that server. However, in DMs, `[user]` will be converted to any user Zephyrus shares a server "
             "with, if possible."
    )
    async def avatar(self, ctx: commands.Context, *, user: str = None):
        if not user:
            user = ctx.author
        else:
            user = user.replace("\n", "")
            try:
                user = await commands.MemberConverter().convert(ctx, user)
            except commands.BadArgument:
                if not ctx.guild:
                    raise commands.CommandError(
                        f"User `@{user}` not found." + (
                            "\nThis looks like a valid username + discriminator, which means this user probably doesn't "
                            "share a server with Zephyrus. Due to a Discord limitation, I can't see users I don't share "
                            "servers with." if re.search(r"#[0-9]{4}$", user) else ""
                        )
                    )
                if len(ctx.guild.members) > 1000:
                    try:  # more blunt method for large servers, in which lcs() takes too long
                        user = [g for g in ctx.guild.members if g.name.lower() == user.lower()][0]
                    except IndexError:
                        raise commands.CommandError(
                            f"User `@{user}` not found.\n"
                            f"This server is large, so please specify their username exactly, or just ping them."
                        )
                else:
                    user = find_user(ctx.guild, user)

        av_url = str(user.avatar.url)
        display_name = user.display_name if ctx.guild else str(user)
        return await ctx.send(
            embed=construct_embed(author=author_from_user(user, name=f"{display_name}'s Avatar", url=av_url),
                                  color=user.colour, image=av_url)
        )

    @commands.command(
        aliases=["sherriff"], usage="z!sheriff <emoji>",
        description="Calls the sheriff of an emoji.",
        help="Calls the sheriff of `<emoji>`."
    )
    async def sheriff(self, ctx: commands.Context, emote: str):
        name = interpret_potential_emoji(self.bot, emote)
        return await ctx.send("⠀ ⠀ ⠀  :cowboy:\n　   {0}\u2060{0}\u2060{0}\n    {0}   {0}　{0}\n"
                              "   :point_down:  {0} {0} :point_down:\n"
                              "  　  {0}　{0}\n　   {0}　 {0}\n　   :boot:     :boot:\nhowdy. {1}"
                              .format(emote, "the name's mccree" if ord(emote[0]) == int("1f55b", 16) else
                                      f"i'm the sheriff of {name.lower()}"))

    @commands.command(
        aliases=["wiki"], usage="z!wikipedia <search...>",
        description="Searches Wikipedia.",
        help="Searches Wikipedia for `<search>`."
    )
    async def wikipedia(self, ctx: commands.Context, *, title: str):
        parser = wk.WikiParser()
        parser.feed(wk.readurl(wk.wikiSearch.format("+".join(title.split()))))
        try:
            return await WikiNavigator(self.bot, *parser.results).run(ctx)
        except IndexError:
            return await wiki.send(ctx, "No results found.")

    @commands.command(
        aliases=["fw"], usage="z!foreignwiki <language> <title...>\nz!foreignwiki all <title...>",
        description="Finds non-English mirrors of a Wikipedia article.",
        help="`z!foreignwiki <language> <title...>` finds the `<language>` version of the English Wikipedia "
             "article `<title>`.\n`z!foreignwiki all <title...>` lists all languages which have a version "
             "of `<title>`."
    )
    async def foreignwiki(self, ctx: commands.Context, lang: str, *, title: str):
        parser = wk.ForeignParser()
        try:
            parser.feed(wk.readurl(wk.wikilink.format("_".join(title.split()))))
        except HTTPError:
            raise commands.CommandError("Article not found in English.")
        if lang.casefold() == "all":
            return await Navigator(self.bot, wiki, [parser.form(g) for g in parser.lang_link], 8,
                                   "Foreign titles of " + parser.title + " [{page}/{pgs}]").run(ctx)
        lang = parser.code_lang.get(lang.lower(), lang.title())
        try:
            return await wiki.send(ctx, parser.lang_title[lang], url=parser.lang_link[lang])
        except KeyError:
            raise commands.CommandError(f"Article unavailable in {lang}.")

    @commands.command(
        usage="z!sampa <X-SAMPA text...>",
        description="Converts X-SAMPA to IPA.",
        help="Converts a given string of [X-SAMPA](https://en.wikipedia.org/wiki/X-SAMPA) to the International "
             "Phonetic Alphabet. `*` can be used as an escape character."
    )
    async def sampa(self, ctx: commands.Context, *, text: str):
        return await ctx.send(content=convert_x_sampa(text))

    @commands.command(
        aliases=["fac"], usage="z!factors <integer>",
        description="Finds the prime factors of a number.",
        help="Returns the prime factors of `<integer>`."
    )
    async def factors(self, ctx: commands.Context, number: int):
        if number < 1:
            raise commands.CommandError("Number must be greater than 0.")
        if log10(number) >= 25:
            raise commands.CommandError("Please keep numbers to 25 digits or less.")

        def get_factors(n: int):
            fac_dic = factorint(n)
            return [g for j in [[k] * v for k, v in fac_dic.items()] for g in j]

        return await ClientEmol(":1234:", blue, ctx).say(
            f"Prime factors of {number}:", d=f"`= {get_factors(number)}`")

    @commands.command(
        name="base", usage="z!base <base> <base-10 integer>\nz!base <to> <integer> <from>",
        description="Converts integers between bases.",
        help="`z!base <base> <base-10 integer>` converts a base-10 (a regular number with digits 0-9) integer to a "
             "given base.\n`z!base <to> <integer> <from>` converts an integer of any base to any other base. Note that "
             "Zephyrus can only use bases between 2 and 36, inclusive.\n\n"
             "`z!base 2 19` → `10011`\n`z!base 10 11001 2` → `25`\n`z!base 16 792997` → `C19A5`"
    )
    async def base_command(self, ctx: commands.Context, to_base: int, num: str, from_base: int = 10):
        if to_base not in range(2, 37) or from_base not in range(2, 37):
            raise commands.CommandError("Base must be between 2 and 36, inclusive.")

        try:
            ret = rebase(num.lower(), from_base, to_base).upper()
        except IndexError:
            raise commands.CommandError(f"{num.upper()} is not a base-{from_base} number.")

        subscript = "".join(chr(ord(g) - 48 + 8320) for g in str(from_base))

        return await ClientEmol(":1234:", blue, ctx).say(ret, d=f"is ({num.upper()}){subscript} in base {to_base}.")

    @commands.command(
        name="age", usage="z!age [@user]",
        description="Shows you how old an account is.",
        help="Shows you how old the given account is, and when they joined the server. If `[@user]` is none, "
             "defaults to your account."
    )
    async def age_command(self, ctx: commands.Context, user: discord.Member = None):
        if not user:
            user = ctx.author

        age_emol = ClientEmol(":hourglass:", hex_to_color("ffac33"), ctx)
        if ctx.guild:
            return await age_emol.say(
                f"{user.display_name}'s Age",
                d=f"This account was created on **{user.created_at.date().strftime('%B %d, %Y').replace(' 0', ' ')}**"
                f".\n{'You' if user == ctx.author else 'They'} "
                f"joined this server on **{user.joined_at.date().strftime('%B %d, %Y').replace(' 0', ' ')}**."
            )
        else:
            return await age_emol.say(
                f"You created your account on **{ctx.author.created_at.date().strftime('%B %d, %Y').replace(' 0', ' ')}**."
            )

    @commands.command(
        name="emoji", aliases=["emote", "e"], usage="z!emoji [emote(s)...]",
        description="Sends a custom emoji.",
        help="`z!e <emote>` returns the input custom emote, if Zeph has one by that name. If you want to search for an "
             "emote, use `z!esearch`.\n\nNote that emote names are *case-sensitive*. For a line break, write `\\n`."
    )
    async def emote_command(self, ctx: commands.Context, *args: str):
        if not args:
            raise commands.CommandError(
                "I deprecated the full emote list because it got slightly too obnoxious.\n"
                "Use `z!esearch <emote>` to look for specific emotes."
            )

        else:
            for arg in args:
                if arg not in self.bot.all_emojis and arg != "\\n":
                    if len(args) == 1:
                        raise commands.CommandError("I don't have that emote.")
                    else:
                        raise commands.CommandError(f"I don't have the `{arg}` emote.")
            try:
                await ctx.send("".join("\n" if g == "\\n" else str(self.bot.all_emojis[g])for g in args))
            except discord.errors.HTTPException:
                raise commands.CommandError("I can't fit that many emotes in one message.")

    @commands.command(
        name="react", aliases=["r"], usage="z!react <emote>\nz!react <message link> <emote>", hidden=True,
        description="Reacts to a message.",
        help="`z!r <emote>` reacts to the message immediately above yours with the input emote. You can also reply "
             "to a message (using Discord's new reply feature) with `z!r <emote>`, and it will react to that message. "
             "Finally, you can also give a message URL (right-click and hit Copy Message Link), and it will react to "
             "the linked message. Then, you yourself can react with that emote, and Zeph's will disappear - it'll "
             "look like you just used Nitro to react.\n\n"
             "If you don't react, Zeph's reaction will disappear after a short while.\n\n"
             "Note that emote names are *case-sensitive*."
    )
    async def react_command(self, ctx: commands.Context, *args: str):
        if len(args) > 2 or len(args) < 1:
            raise commands.BadArgument

        if args[-1].strip(":") not in self.bot.all_emojis:
            if args[0].strip(":") in self.bot.all_emojis:
                args = args[1], args[0]
            else:
                raise commands.CommandError("I don't have that emote.")
        emote = self.bot.all_emojis[args[-1].strip(":")]

        if len(args) == 1:
            pointer = "^"
        else:
            pointer = args[0]

        if ctx.message.reference:  # if the message is a reply to another message
            if len(args) == 2:
                raise commands.CommandError("Either reply to a message, OR give a URL. Don't do both.")
            ref = ctx.message.reference
            if ref.cached_message:  # check for the cached message first, it'll be faster
                mess = ref.cached_message
            else:  # if not, try to manually fetch the referenced message
                try:
                    mess = await self.bot.get_channel(ref.channel_id).fetch_message(ref.message_id)
                except discord.HTTPException:
                    raise commands.CommandError("I couldn't find the referenced message, sorry.")

        else:
            mess = await get_message_pointer(ctx, pointer, fallback=ctx.message)

        await mess.add_reaction(emote)

        def pred(r: discord.RawReactionActionEvent):
            return r.emoji == emote and r.message_id == mess.id and r.user_id == ctx.author.id

        try:
            await self.bot.wait_for('raw_reaction_add', timeout=30, check=pred)
        except asyncio.TimeoutError:
            pass

        await mess.remove_reaction(emote, self.bot.user)  # remove zeph's reaction once the user has also reacted
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @commands.command(
        aliases=["rw"], usage="z!randomword [pattern]",
        description="Generates a random word.",
        help="Generates a random word made of IPA symbols. If `[pattern]` is not specified, defaults to CVCVCVCV.\n\n"
             "Valid pattern letters are: **`C`** for consonants, **`F`** for fricatives, **`J`** for palatals, **`K`** "
             "for clicks, **`L`** for laterals, **`N`** for nasals, **`P`** for plosives, **`R`** for rhotics, **`S`** "
             "for sibilants, **`T`** for taps, **`U`** for all vowels, **`V`** for the five basic vowels [a e i o u], "
             "**`W`** for approximants, and **`X`** for trills."
    )
    async def randomword(self, ctx: commands.Context, pattern: str = "CVCVCVCV"):
        """Stolen pretty much directly from Leo (https://github.com/Slorany/LeonardBot)."""

        subs = {
            "A": "",
            "B": "",
            "C": "pbtdʈɖcɟkgqɢʔmɱnɳɲŋɴʙrʀɾɽɸβfvθðszʃʒʂʐçʝxɣχʁħʕhɦɬɮʋɹɻjɰlɭʎʟ",  # consonants
            "D": "",
            "E": "",
            "F": "ɸβfvθðszʃʒʂʐçʝxɣχʁħʕhɦɬɮ",  # fricatives
            "G": "",
            "H": "",
            "I": "",
            "J": "cɟɲçʝjʎɕʑ",  # palatals
            "K": "ǁǂǃǀʘ",  # clicks
            "L": "ʟʎlɬɮɭɺ",  # laterals
            "M": "",
            "N": "mɱnɳɲŋɴ",  # nasals
            "O": "",
            "P": "pbtdʈɖcɟkgqɢʔ",  # plosives
            "Q": "",
            "R": "rɾɹɻʀʁɽɺ",  # rhotics
            "S": "szʃʒʂʐ",  # sibilants
            "T": "ɾɽɺ",  # taps / flaps
            "U": "iyɨʉɯuɪʏʊeøɘɵɤoəɛœɜɞʌɔæɐaɶɑɒ",  # all vowels
            "V": "aeiou",  # the basic five vowels
            "W": "ʋɹɻjɰlɭʎʟwʍɥ",  # approximants
            "X": "ʙrʀ",  # trills
            "Y": "",
            "Z": ""
        }

        def choose_sub(s: str): return "" if not len(subs.get(s, s)) else random.choice(subs[s]) if subs.get(s) else s

        ret = "".join(choose_sub(c) for c in pattern)
        if not ret:
            raise commands.CommandError("Pattern would be empty. Do `z!help rw` for a list of valid sets.")
        return await ctx.send(ret)

    @commands.command(
        aliases=["stest", "st"], usage="z!syntaxtest [number 1-218]\nz!syntaxtest list",
        description="Gives you a sentence to test conlang syntax.",
        help="`z!stest` returns a random sentence from the [list of 218 conlang syntax test sentences]"
             "(https://web.archive.org/web/20120427054736/http://fiziwig.com/conlang/syntax_tests.html).\n"
             "`z!stest <number 1-218>` returns sentence #`number`.\n"
             "`z!stest list` links a full list of the sentences."
    )
    async def syntaxtest(self, ctx: commands.Context, arg: str = None):
        """This is also taken from Leo (see randomword, above)."""

        if not arg:
            return await ctx.send(random.choice(stest_sentences))

        if str(arg).lower() == "list":
            return await ctx.send("Here's a list of the 218 syntax test sentences: <http://pastebin.com/raw/BpfjThwA>")

        try:
            int(arg)
        except ValueError:
            raise commands.BadArgument
        else:
            if int(arg) < 1 or int(arg) > 218:
                raise commands.BadArgument
            else:
                return await ctx.send(stest_sentences[int(arg) - 1])

    @commands.command(
        aliases=["rm"], usage="z!rolemembers <role>",
        description="Lists all the members of a certain role.",
        help="`z!rm <role>` returns a scrollable list of all server members who have a given role, along with a count."
    )
    async def rolemembers(self, ctx: commands.Context, *, role_name: str):
        """Another command idea taken from Leo, but this one is heavily adapted from the original."""

        possible_roles = [g for g in ctx.guild.roles if g.name.lower() == role_name.lower()]
        emol = Emol(":clipboard:", hex_to_color("C1694F"))

        if len(possible_roles) == 0:
            if not ctx.guild.roles:
                raise commands.CommandError("There's no roles in this server.")

            dym = sorted(ctx.guild.roles, key=lambda c: modified_lcs(c.name, role_name))
            raise commands.CommandError(f"`{role_name}` role not found.\nDid you mean {dym[0].mention}?")

        if len(possible_roles) > 1:  # fuck you manti
            await emol.send(ctx, f"There are multiple roles called `{role_name}`.",
                            d="Use the :arrows_clockwise: button to cycle between them.")

        return await RMNavigator(self.bot, sorted(possible_roles, key=lambda c: -len(c.members))).run(ctx)

    @commands.command(
        name="remindme", aliases=["remind", "reminder", "rme", "rem"],
        usage="z!remindme <reminder...> in <time...>\nz!remindme list",
        description="Reminds you of something later.",
        help="`z!remindme <reminder> in <time>` sets the bot to DM you with a reminder in a certain amount of time. "
             "`<reminder>` can be anything. `<time>` can use any combination of integer years, months, weeks, days, hours, "
             "or minutes, separated by spaces. Several abbreviations (e.g. `yr` for year) can also be "
             "used.\n\n`z!remindme list` lists your set reminders, and lets you remove any if need be. **Make sure your "
             "DMs are open, or else the reminder won't send.**\n\n"
             "e.g. `z!remindme eat food in 2 hours`, `z!rme work on essay in 5 hours 30 minutes`, or "
             "`z!remind talk to Sam in 3 days`."
    )
    async def remind_command(self, ctx: commands.Context, *, text: str):
        if text.lower() in ["list", "edit", "remove", "delete"]:
            if not [g for g in self.bot.reminders if g.author == ctx.author.id]:
                return await Emol(":alarm_clock:", hex_to_color("DD2E44")).send(ctx, "You have no reminders set currently.")

            return await RemindNavigator(self.bot, ctx.author).run(ctx)

        if not ctx.author.dm_channel:
            try:
                await ctx.author.create_dm()
            except discord.HTTPException:
                raise commands.CommandError("I can't DM you! Are your DMs open?\n`z!remindme` uses DMs to send reminders.")

        # https://regex101.com/r/exJpFT/1
        regex = r"(in |^)((?P<years>[0-9]+) ?y(ear|r|)s?(,? |$))?((?P<months>[0-9]+) ?m(onth|o)s?(,? |$))?" \
                r"((?P<weeks>[0-9]+) ?w(eek|k|)s?(,? |$))?((?P<days>[0-9]+) ?d(ay|)s?(,? |$))?" \
                r"((?P<hours>[0-9]+) ?h(our|r|)s?(,? |$))?((?P<minutes>[0-9]+) ?m(inute|in|)s?( |$))?"

        for match in re.finditer(regex, text):
            if len(match[0]) > 3:
                groups = match.groupdict(default=0)
                years = int(groups.get("years", 0))
                months = int(groups.get("months", 0))
                weeks = int(groups.get("weeks", 0))
                days = int(groups.get("days", 0))
                hours = int(groups.get("hours", 0))
                minutes = int(groups.get("minutes", 0))
                reminder = text[:match.start()] + text[match.end():]
                break
        else:
            raise commands.CommandError("No time given.")

        if not reminder:
            reminder = ctx.message.jump_url
        else:
            reminder += f" ({ctx.message.jump_url})"

        from_datetime = datetime.datetime.now()
        if months or years:
            current_date = datetime.date.today()
            new_year = current_date.year + years + (months + current_date.month - 1) // 12
            new_month = (months + current_date.month - 1) % 12 + 1
            try:
                future_date = datetime.date(new_year, new_month, current_date.day)
            except ValueError:
                future_date = datetime.date(new_year, new_month, 28)
                days += current_date.day - 28
            from_datetime = from_datetime.replace(year=future_date.year, month=future_date.month, day=future_date.day)

        timestamp = round(from_datetime.timestamp() + weeks * 604800 + days * 86400 + hours * 3600 + minutes * 60)

        reminder = Reminder(ctx.author.id, reminder, timestamp)

        if years + months + weeks + days + hours + minutes == 0:
            await success.send(ctx, "Alright, wiseguy, I'll send it right now.")
            try:
                return await reminder.send(self.bot)
            except discord.HTTPException:
                raise commands.CommandError("Never mind, I can't DM you. Are your DMs open?")

        self.bot.reminders.append(reminder)

        return await success.send(
            ctx, "Reminder added!", d=f"I'll remind you <t:{timestamp}:R>."
        )

    @commands.command(
        name="weather", aliases=["w"], usage="z!weather <location...>",
        description="Shows the weather somewhere.",
        help="Shows the weather in `<location>` - condition, temperature, highs and lows, rain chance, etc. "
             "Weather data might be delayed by a couple minutes.\n\n"
             "`<location>` is converted to an actual place by [Google's geocoding API]"
             "(https://developers-dot-devsite-v2-prod.appspot.com/maps/documentation/utils/geocoder) (like `z!timein`)."
    )
    async def weather_command(self, ctx: commands.Context, *, location: str):
        def heading_direction(heading: float):
            dirs = [
                "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW", "N"
            ]
            return dirs[round(heading * 16 / 360)]

        def format_kelvin(k: float):
            return f"**{ti.fahr(k)}° F** (**{round(k - 273.15)}° C**)"

        def conditions(r: dict):
            return "; ".join(
                f"{[e for e, v in weather_emotes.items() if g['id'] in v][0]} {g['description']}"
                for g in r['current']['weather']
            )

        try:
            lat_long = ti.lat_long(location)
        except IndexError:
            raise commands.CommandError("Location not found.")

        mess = await Emol(self.bot.emojis["loading"], hex_to_color("65747E")).send(ctx, "Fetching weather data...")

        attempts = 0
        while True:
            attempts += 1
            req = requests.get(ti.weather_url.format(**lat_long, key=api_keys.open_weather))
            if req.status_code >= 500:
                if attempts == 3:
                    raise commands.CommandError(f"Something went wrong.\nHTTP status: `{req.status_code}`")
                await Emol(self.bot.emojis["loading"], hex_to_color("65747E")).edit(
                    mess, "Something went wrong. Trying again...",
                    d=f"In the words of Google, don't fret - it's not your fault. I'll try {3 - attempts} more "
                      f"{plural('time', 3 - attempts)}."
                )
                continue
            elif req.status_code >= 300:
                raise commands.CommandError("Something went wrong.\nHTTP status: `{req.status_code}`")
            else:
                break
        req = req.json()

        weather_emotes = {  # weather condition codes to emotes
            ":sunny:": (800, ),
            ":white_sun_small_cloud:": (801, ),
            ":partly_sunny:": (802, ),
            ":white_sun_cloud:": (803, ),
            ":cloud:": (701, 711, 721, 731, 741, 751, 761, 804),
            ":thunder_cloud_rain:": (200, 201, 202, 210, 211, 212, 221, 230, 231, 232),
            ":cloud_rain:": (300, 301, 302, 310, 311, 312, 313, 314, 321, 500, 501, 502, 503, 504, 520, 521, 522, 531),
            ":cloud_snow:": (511, ),
            ":snowflake:": (600, 601, 602, 611, 612, 613, 615, 616, 620, 621, 622),
            ":volcano:": (762, ),  # volcanic ash
            ":dash:": (771, ),  # squalls
            ":tornado:": (781, )  # self-explanatory
        }

        return await Emol(":umbrella2:", hex_to_color("9266CC")).edit(
            mess, f"Weather in {ti.short_placename(location)}",
            d=f"**{conditions(req)}** / :thermometer: {format_kelvin(req['current']['temp'])}\n---\n"
            f":sweat_drops: humidity: **{req['current']['humidity']}%** / "
            f":thought_balloon: feels like: {format_kelvin(req['current']['feels_like'])}\n"
            f":wind_blowing_face: wind: ** {heading_direction(req['current']['wind_deg'])} "
            f"{round(req['current']['wind_speed'] * 2.23693629)} mph** "
            f"(**{round(req['current']['wind_speed'] * 3.6)} kph**)\n---\n"
            f":fire: daily high: {format_kelvin(req['daily'][0]['temp']['max'])} / "
            f":ice_cube: low: {format_kelvin(req['daily'][0]['temp']['min'])}\n"
            f":umbrella: rain chance: **{round(req['daily'][0]['pop'] * 100)}%**",
            timestamp=datetime.datetime.fromtimestamp(req['current']['dt'], datetime.timezone.utc),
            footer=ti.placename(location)
        )

    @commands.command(
        name="role", usage="REDIRECT", hidden=True
    )
    async def role_redirect_command(self, ctx: commands.Context):
        return await lost.send(
            ctx, "You might be looking for...",
            d="**`role`** might refer to multiple commands:\n"
              "- `z!selfroles`, which lets you self-assign roles.\n"
              "- `z!rolemembers`, which lists all the members of a role."
        )

    @commands.command(
        name="counter", aliases=["count"], usage="z!counter [starting value] [increment]",
        description="Runs a counter, so you can count.",
        help="Runs a simple counter. Count up or down by an adjustable value using the reaction buttons. I wouldn't "
             "recommend using this command if you have to repeatedly and *quickly* change the value, however; due to "
             "Discord's rate limits, some of your clicks might get lost. Optional arguments are the value the counter "
             "at, which defaults to 0, and the increment to be counted by, which defaults to 1."
    )
    async def counter_command(self, ctx: commands.Context, start_value: int = 0, increment: int = 1):
        return await CounterNavigator(self.bot, start_value, increment).run(ctx)

    @commands.command(
        name="esearch", aliases=["es"], usage="z!esearch <emote name>",
        description="Searches for an emote.",
        help="Searches for an emote by name. Returns a scrollable list of similarly-named emotes Zeph has access to, "
             "for use with `z!e` and `z!r`."
    )
    async def emote_search_command(self, ctx: commands.Context, *, query: str = ""):
        emol = Emol(self.bot.emojis["search"], hex_to_color("83BEEC"))
        scd = {g: modified_lcs(g, query.replace(" ", "_")) for g in self.bot.all_emojis}  # single calc of modified_lcs
        emotes = sorted([g for g, j in scd.items() if j <= 2 + (32 - len(query) / 2)], key=lambda k: scd[k])
        await Navigator(self.bot, emol, [f"`:{g}:` ({self.bot.all_emojis[g]})" for g in emotes],
                        8, "Emote List [{page}/{pgs}]").run(ctx)

    @commands.command(
        name="coinflip", aliases=["flip", "coin", "cf"], usage="z!coinflip",
        help="Flips a coin."
    )
    async def coinflip_command(self, ctx: commands.Context):
        return await ctx.send(
            f"{self.bot.emojis['coinheads']} **Heads!**" if random.random() < 0.5
            else f"{self.bot.emojis['cointails']} **Tails!**"
        )

    @commands.command(
        name="hug", aliases=["hugs"], usage="z!hug [user]",
        help="Hugs you, or a friend."
    )
    async def hug_command(self, ctx: commands.Context):
        return await ctx.send(":hugging:")

    @commands.command(
        name="cases", aliases=["case", "grammar"], usage="z!cases",
        hidden=True
    )
    async def cases_command(self, ctx: commands.Context):
        return await ctx.send("<https://en.wikipedia.org/wiki/List_of_grammatical_cases>")
