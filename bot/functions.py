import asyncio
import discord
import random
import re
from discord.ext import commands
from functools import partial


def plural(s: str, n: float | int, **kwargs):
    """Pluralizes a noun if n != 1. 'plural' kwarg allows alternative plural form."""
    return kwargs.get("plural", s + kwargs.get("suffix", "s")) if n != 1 else s


def a_or_an(s: str) -> str:
    return f"a{'n' if s.strip('*_ ')[0].lower() in 'aeiou' else ''} {s}"


def none_list(ls: list | tuple, joiner: str = ", ", if_empty: str = "none"):
    return joiner.join(ls) if ls else if_empty


def grammatical_join(ls: list, conj: str = "and"):
    if len(ls) <= 2:
        return f" {conj} ".join(ls)
    else:
        return f"{', '.join(ls[:-1])}, {conj} {ls[-1]}"


def caseless_match(s: str, database: iter) -> str | None:
    try:
        return [g for g in database if str(g).lower() == s.lower()][0]
    except IndexError:
        return None


def can_use_without_error(func: callable, arg, error_type=ValueError):
    try:
        func(arg)
    except error_type:
        return False
    return True


def can_int(s: str):
    if not isinstance(s, (str, int, float)):
        return False
    return can_use_without_error(int, s)


def snip(s: str, n: int, from_back: bool = False):  # breaks string into n-long pieces
    if not from_back:
        return [s[n * m:n * (m + 1)] for m in range(ceil(len(s) / n))]
    else:
        return list(reversed([s[-n:]] + [s[-n * (m + 1):-n * m] for m in range(1, ceil(len(s) / n))]))


def add_commas(n: float | int | str):
    if "e" in str(n):
        return str(n)
    n = str(n).split(".")
    if len(n[0]) < 5:
        return ".".join(n)
    n[0] = ",".join(snip(n[0], 3, True))
    return ".".join(n)


def should_await(func: callable):
    if isinstance(func, partial):
        return asyncio.iscoroutinefunction(func.func)
    else:
        return asyncio.iscoroutinefunction(func)


def hex_to_color(hex_code: str):
    if int(hex_code, 16) < 0:
        raise ValueError("negative hexcol code")
    if int(hex_code, 16) > 16777215:
        raise ValueError("hexcol int should be less than 16777215")
    return discord.Colour(int(hex_code, 16))


def levenshtein(s1, s2, insert_cost: int = 1, delete_cost: int = 1, sub_cost: int = 1):  # ripped from Wikipedia
    if len(s1) < len(s2):
        return levenshtein(s2, s1, insert_cost, delete_cost, sub_cost)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + insert_cost
            deletions = current_row[j] + delete_cost
            substitutions = previous_row[j] + (c1 != c2) * sub_cost
            current_row.append(min((insertions, deletions, substitutions)))
        previous_row = current_row

    return previous_row[-1]


def best_guess(target: str, possibilities: iter):
    di = {g: levenshtein(target, g.lower()) for g in possibilities}
    return random.choice([key for key in di if di[key] == min(list(di.values()))])


def admin_check(ctx: commands.Context):
    if ctx.author.id not in [238390171022655489, 474398677599780886]:
        raise commands.CommandError("You don't have permission to run that command.")


def general_pred(ctx: commands.Context) -> callable:
    return lambda m: m.author == ctx.author and m.channel == ctx.channel


def fix(s: str, joiner: str = "-"):
    return re.sub(f"{joiner}+", joiner, re.sub(f"[^a-z0-9{joiner}]+", "", re.sub(r"\s+", joiner, s.lower().replace("é", "e"))))


lower_alphabet = "abcdefghijklmnopqrstuvwxyz"
small_alphabet = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"


def smallcaps(s: str):
    if s.isupper():
        return smallcaps(s.lower())

    alpha_dict = {"\u00e9": "ᴇ́", **{lower_alphabet[g]: small_alphabet[g] for g in range(26)}}
    return "".join([alpha_dict.get(g, g) for g in s])


def yesno(b: bool):
    return "yes" if b else "no"
