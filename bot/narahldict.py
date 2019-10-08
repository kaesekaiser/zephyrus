from planes import *
from typing import Union
import re


class PartOfSpeech:
    def __init__(self, *defs: str):
        self.defs = defs

    def __getitem__(self, item: int):  # part[1] returns first definition, more intuitive in this case
        return self.defs[item - 1]

    def __str__(self):
        return "\n".join(f"\u00a0\u00a0\u00a0**{n + 1}.** {self.defs[n]}" for n in range(len(self.defs)))

    @staticmethod
    def from_str(s: str):
        ret = s.strip("# ").split(" # ")
        return PartOfSpeech(
            *[re.sub(r"\s\*+(?=\s)", lambda m: "\n" + "\u00a0" * (6 * (len(m[0]) - 1) + 3) + "•", g) for g in ret]
        )

    def json(self):
        ret = [re.sub(r"\n\s+•", lambda m: " " + "*" * ((len(m[0]) - 2) // 6), g, re.M) for g in self.defs]
        return " # ".join(ret)


class Entry:
    def __init__(self, abbrev: str, parts: dict, tags: list = ()):
        self.abbrev = abbrev
        self.parts = {g: PartOfSpeech.from_str(j) if isinstance(j, str) else j for g, j in parts.items()}
        self.tags = list(tags)

    def __getitem__(self, item: Union[str, tuple]):
        if isinstance(item, str):
            return self.parts[item]
        elif isinstance(item, tuple):
            return self.parts[item[0]][item[1]]

    def __str__(self):
        return "\n".join(f"**{g}.**\n{j}" for g, j in self.parts.items())

    @staticmethod
    def from_str(s: str):
        try:
            parts, tags = re.split(r" @ ", s, 1)
        except ValueError:
            parts, tags = s, []
        abbrev, parts = parts.split(" = ")
        return Entry(
            abbrev, dict([g.split(" : ") for g in parts.split(" | ")]),
            tags.split(" @ ") if isinstance(tags, str) else tags
        )

    def save(self):
        ret = [f"{g} : {j.json()}" for g, j in self.parts.items()]
        return f"{self.abbrev} = {' | '.join(ret)} @ {' @ '.join(self.tags)}"


class NarahlInterpreter(Interpreter):
    redirects = {"s": "search", "f": "find", "a": "add", "b": "browse", "h": "help", "e": "edit"}
    emol = Emol(":book:", hexcol("226699"))

    @staticmethod
    def levenshtein(s1, s2):  # ripped from Wikipedia
        if len(s1) < len(s2):
            return NarahlInterpreter.levenshtein(s2, s1)

        if len(s2) == 0:
            return len(s1)

        close_enough = {"c", "ç"}, {"c", "č"}, {"č", "ç"}, {"a", "ā"}, {"a", "â"}, {"â", "ā"}, {"o", "ô"}, {"u", "û"}, \
            {"s", "š"}, {"z", "ž"}, {"n", "ň"}
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2) * (0.5 if {c1, c2} in close_enough else 1)
                current_row.append(min((insertions, deletions, substitutions)))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def save_ndict():
        with open("storage/ndict.txt", "w", encoding="utf-8") as fip:
            fip.write("\n".join(f"{g} = {j.save()}" for g, j in ndict.items()))

    async def _help(self, *args):
        help_dict = {
            "search": "`z!ndict search <term>` searches the dictionary for words related to <term>. For example, "
                      "`z!ndict s color` will return words that mean \"color\", but also color terms.",
            "find": "`z!ndict find <word>` shows the definition for a given word in the dictionary.",
            "browse": "`z!ndict browse` lets you flip through the alphabetized dictionary."
        }
        desc_dict = {
            "search": "Searches for related words.",
            "find": "Shows the definition for a specific word.",
            "browse": "Flips through the whole dictionary."
        }
        shortcuts = {j: g for g, j in self.redirects.items() if len(g) == 1}

        def get_command(s: str):
            return f"**`{s}`** (or **`{shortcuts[s]}`**)" if shortcuts.get(s) else f"**`{s}`**"

        if not args or args[0].lower() not in help_dict:
            return await self.emol.send(
                self.ctx, "z!ndict help",
                d="Available functions:\n\n" + "\n".join(f"{get_command(g)} - {j}" for g, j in desc_dict.items()) +
                  "\n\nFor information on how to use these, use ``z!ndict help <function>``."
            )

        return await self.emol.send(self.ctx, f"z!ndict {args[0].lower()}", d=help_dict[args[0].lower()])

    async def _search(self, *args):
        search = " ".join(args).lower()
        abb_match = [g for g, j in ndict.items() if search in j.abbrev.lower()]
        def_match = [g for g, j in ndict.items() if re.search("[^a-z]" + search + "[^a-z]", str(j).lower())]
        tag_match = [g for g, j in ndict.items() if search in j.tags]
        bad_match = [g for g, j in ndict.items() if set(args).intersection(set(j.tags))]
        order = [
            set(abb_match).intersection(def_match).intersection(tag_match),
            set(abb_match).intersection(def_match),
            set(abb_match).intersection(tag_match),
            set(abb_match),
            set(def_match).intersection(tag_match),
            set(def_match),
            set(tag_match),
            set(bad_match)
        ]
        ret = []
        for st in order:
            for match in st:
                if match not in ret:
                    ret.append(match)
        return await Navigator(
            self.emol, [f"- **{g}** (\"{ndict[g].abbrev}\")" for g in ret], 6,
            "Results for \"" + search + "\" [{page}/{pgs}]"
        ).run(self.ctx)

    async def _find(self, *args):
        word = " ".join(args).lower()
        if word in ndict:
            return await self.emol.send(self.ctx, word, d=str(ndict[word]))
        else:
            guess = sorted(list(ndict.keys()), key=lambda c: self.levenshtein(word, c))
            return await self.emol.send(
                self.ctx, f"\"{word}\" not found.",
                d="Did you mean?\n - " + "\n - ".join(guess[:5])
            )

    async def _browse(self, *args):
        return await Navigator(
            self.emol, [f"- **{g}** (\"{ndict[g].abbrev}\")" for g in sorted(list(ndict.keys()))], 10,
            "Narahlena Lexicon [{page}/{pgs}]"
        ).run(self.ctx)

    async def _add(self, *args):
        admin_check(self.ctx)

        word = ascii_narahlena(" ".join(args))
        if word in ndict:
            raise commands.CommandError(f"`word` is already defined.")

        def pred(m: discord.Message):
            return m.author == self.ctx.author and m.channel == self.ctx.channel

        while True:
            await self.emol.send(self.ctx, f"What is the abbreviated definition of `{word}`?")
            try:
                abb = await zeph.wait_for("message", check=pred, timeout=600)
            except asyncio.TimeoutError:
                raise commands.CommandError("Definition timed out.")
            abb = abb.content
            try:
                assert await confirm(
                    "Is this correct?", self.ctx, emol=self.emol, add_info=f"**{word}** (\"{abb}\")\n\n"
                )
            except AssertionError:
                continue
            else:
                break

        while True:
            await self.emol.send(self.ctx, f"What is the full definition of `{word}`?")
            try:
                dfn = await zeph.wait_for("message", check=pred, timeout=600)
            except asyncio.TimeoutError:
                raise commands.CommandError("Definition timed out.")
            entry = Entry.from_str(f"{abb} = {dfn.content}")
            try:
                assert await confirm("Is this correct?", self.ctx, emol=self.emol, add_info=f"{entry}\n\n")
            except AssertionError:
                continue
            else:
                break

        while True:
            await self.emol.send(self.ctx, f"What should `{word}` be tagged?", d="Separate tags with ` @ `.")
            try:
                tag = await zeph.wait_for("message", check=pred, timeout=600)
            except asyncio.TimeoutError:
                raise commands.CommandError("Tags timed out.")
            if tag.content.lower() != "none":
                entry.tags.extend(tag.content.lower().split(" @ "))
            try:
                assert await confirm("Are these correct?", self.ctx, emol=self.emol, add_info=f"{entry.tags}\n\n")
            except AssertionError:
                continue
            else:
                break

        ndict[word] = entry
        self.save_ndict()
        return await succ.send(self.ctx, f"`{word}` added.")

    async def _edit(self, *args):
        admin_check(self.ctx)
        
        if len(args) < 2:
            raise commands.CommandError("Format: `z!nd e <word> <abb | def | tags>`")

        word = ascii_narahlena(args[0].lower())
        if word not in ndict:
            guess = sorted(list(ndict.keys()), key=lambda c: self.levenshtein(word, c))
            return await self.emol.send(
                self.ctx, f"\"{word}\" not found.",
                d="Did you mean?\n - " + "\n - ".join(guess[:5])
            )

        def pred(m: discord.Message):
            return m.author == self.ctx.author and m.channel == self.ctx.channel

        if args[1].lower() in ["a", "abb"]:
            await self.ctx.send(f"Current abbreviated definition of {word}:\n`{ndict[word].abbrev}`")
            while True:
                await self.emol.send(self.ctx, f"What is the new abbreviated definition of `{word}`?")
                try:
                    abb = await zeph.wait_for("message", check=pred, timeout=600)
                except asyncio.TimeoutError:
                    raise commands.CommandError("Definition timed out.")
                abb = abb.content
                try:
                    assert await confirm(
                        "Is this correct?", self.ctx, emol=self.emol, add_info=f"**{word}** (\"{abb}\")\n\n"
                    )
                except AssertionError:
                    continue
                else:
                    ndict[word].abbrev = abb
                    await succ.send(self.ctx, "Abbreviated definition updated.")
                    break

        elif args[1].lower() in ["d", "def"]:
            await self.ctx.send(f"Current definition of {word}:\n`{ndict[word].save()}`")
            while True:
                await self.emol.send(self.ctx, f"What is the new full definition of `{word}`?")
                try:
                    dfn = await zeph.wait_for("message", check=pred, timeout=600)
                except asyncio.TimeoutError:
                    raise commands.CommandError("Definition timed out.")
                entry = Entry.from_str(f"{ndict[word].abb} = {dfn.content}")
                try:
                    assert await confirm("Is this correct?", self.ctx, emol=self.emol, add_info=f"{entry}\n\n")
                except AssertionError:
                    continue
                else:
                    ndict[word].parts = entry.parts
                    await succ.send(self.ctx, "Definition updated.")
                    break

        elif args[1].lower() in ["t", "tags"]:
            await self.ctx.send(f"Current tags on {word}:\n`{' @ '.join(ndict[word].tags)}`")
            while True:
                await self.emol.send(self.ctx, f"What should `{word}` be tagged?", d="Separate tags with ` @ `.")
                try:
                    tag = await zeph.wait_for("message", check=pred, timeout=600)
                except asyncio.TimeoutError:
                    raise commands.CommandError("Tags timed out.")
                if tag.content.lower() != "none":
                    tags = tag.content.lower().split(" @ ")
                else:
                    tags = []
                try:
                    assert await confirm("Are these correct?", self.ctx, emol=self.emol, add_info=f"{tags}\n\n")
                except AssertionError:
                    continue
                else:
                    ndict[word].tags = tags
                    await succ.send(self.ctx, "Tags updated.")
                    break

        else:
            raise commands.CommandError("Format: `z!nd e <word> <abb | def | tags>`")

        self.save_ndict()


with open("storage/ndict.txt", "r", encoding="utf-8") as fp:
    ndict_temp = [re.split(r" = ", g, 1) for g in fp.readlines()]
    ndict = {g[0]: Entry.from_str(g[1].strip("\n")) for g in ndict_temp}


@zeph.command(
    name="ndict", aliases=["nd"], usage="z!ndict help",
    description="Accesses the Narahlena dictionary.",
    help="Browses, searches, and (if you're Fort) edits the Narahlena dictionary. Use `z!nd help` for more info."
)
async def ndict_command(ctx: commands.Context, func: str = None, *args: str):
    return await NarahlInterpreter(ctx).run(str(func).lower(), *args)
