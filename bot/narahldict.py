from planes import *
from typing import Union
import re
from random import choices


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
        return f"{self.abbrev} = {self.json_def} @ {' @ '.join(self.tags)}"

    @property
    def json_def(self):
        return " | ".join([f"{g} : {j.json()}" for g, j in self.parts.items()])


class NDictNavigator(Navigator):
    @staticmethod
    def alphabetize(s: str):
        return ["aāâbcçčdefghijklmnňoôprsštuvwyzž".index(g) for g in s.lower()]

    def __init__(self):
        lets = "AĀÂBCÇČDEFGHIJKLMNŇOÔPRSŠTUVWYZŽ"
        lex = {g: sorted([j for j in ndict if j.upper()[0] == g], key=self.alphabetize) for g in lets}
        lex = {g: j + [""] * (10 - len(j) % 10) for g, j in lex.items() if j}
        lex = [g for item in [
            [f"- **{v}** (\"{ndict[v].abbrev}\")" if v else "" for v in j]
            for j in lex.values()
        ] for g in item]
        super().__init__(NarahlInterpreter.emol, lex, 10, "Narahlena Lexicon [{letter}]", prev="", nxt="")
        self.funcs["⏪"] = self.back_five
        self.funcs["◀"] = self.back_one
        self.funcs["▶"] = self.forward_one
        self.funcs["⏩"] = self.forward_five

    @property
    def con(self):
        d = none_list(page_list(self.table, self.per, self.page), "\n")
        return self.emol.con(
            self.title.format(letter=d[4].upper() + d[4].lower()),
            d=d, footer=f"page {self.page} of {self.pgs}"
        )

    def back_five(self):
        self.advance_page(-5)

    def back_one(self):
        self.advance_page(-1)

    def forward_one(self):
        self.advance_page(1)

    def forward_five(self):
        self.advance_page(5)


class NarahlInterpreter(Interpreter):
    redirects = {"s": "search", "f": "find", "a": "add", "b": "browse", "h": "help", "e": "edit", "m": "move",
                 "k": "markov"}
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
    def tf_idf(doc: str, query: list):
        doc_words = "".join([g.lower() for g in doc if re.match(r"[a-zA-Z0-9\s]", g)]).split()
        query = [re.sub(r"[^a-zA-Z0-9\s]", "", g).lower() for g in query]
        ret = {}
        for item in query:
            try:
                tf = doc_words.count(item) / len(doc_words)
            except ZeroDivisionError:
                tf = 0
            try:
                idf = log10(len(ndict_corp) / len([g for g in ndict_corp.values() if item in g]))
            except ZeroDivisionError:
                idf = 0
            ret[item] = tf * idf
        return ret

    @staticmethod
    def save_ndict():
        with open("storage/ndict.txt", "w", encoding="utf-8") as fip:
            fip.write("\n".join(f"{g} = {j.save()}" for g, j in ndict.items()))
        NarahlInterpreter.update_corp()

    @staticmethod
    def update_corp():
        for g, j in ndict.items():
            ndict_corp[g] = re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9\s]", "", j.save()).lower()).split()
        for g in list(ndict_corp):
            if g not in ndict:
                del ndict_corp[g]

    @staticmethod
    def sqrt_avg(l: iter):
        return sum(l) / (len(l) ** 0.5)

    async def _help(self, *args):
        help_dict = {
            "search": "`z!ndict search <term>` searches the dictionary for words related to <term>. For example, "
                      "`z!ndict s color` will return words that mean \"color\", but also color terms.",
            "find": "`z!ndict find <word>` shows the definition for a given word in the dictionary.",
            "browse": "`z!ndict browse` lets you flip through the alphabetized dictionary.",
            "markov": "`z!ndict markov [syllables] generates a new Narahlena word using a markov chain based off the"
                      "existing lexicon."
        }
        desc_dict = {
            "search": "Searches for related words.",
            "find": "Shows the definition for a specific word.",
            "browse": "Flips through the whole dictionary.",
            "markov": "Generates a new word."
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
        search = [re.sub(r"[^a-zA-Z0-9\s]", "", g).lower() for g in args]
        res = {
            g: self.sqrt_avg(self.tf_idf(re.sub(r" \* .*?(?= # | \| | @ |$)", "", j.json_def), search).values()) +
            10 * self.sqrt_avg(self.tf_idf(j.abbrev, search).values()) +
            self.sqrt_avg(self.tf_idf(" ".join(j.tags), search).values())
            for g, j in ndict.items()
        }
        ret = sorted([g for g, j in res.items() if j > 0.1], key=lambda c: -res[c])
        return await Navigator(
            self.emol, [f"- **{g}** (\"{ndict[g].abbrev}\")" for g in ret], 6,
            "Results for \"" + " ".join(search) + "\" [{page}/{pgs}]"
        ).run(self.ctx)

    async def _find(self, *args):
        word = ascii_narahlena(" ".join(args).lower())
        if word in ndict:
            return await self.emol.send(self.ctx, word, d=str(ndict[word]))
        else:
            guess = sorted(list(ndict.keys()), key=lambda c: self.levenshtein(word, c))
            return await self.emol.send(
                self.ctx, f"\"{word}\" not found.",
                d="Did you mean?\n - " + "\n - ".join(guess[:5])
            )

    async def _browse(self, *args):
        return await NDictNavigator().run(self.ctx)

    async def _add(self, *args):
        admin_check(self.ctx)

        word = ascii_narahlena(" ".join(args))
        if word in ndict:
            raise commands.CommandError(f"`word` is already defined.")

        def pred(m: discord.Message):
            return m.author == self.ctx.author and m.channel == self.ctx.channel

        while True:
            await self.emol.send(self.ctx, f"What is the abbreviated definition of _{word}_?")
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
            await self.emol.send(self.ctx, f"What is the full definition of _{word}_?")
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
            await self.emol.send(self.ctx, f"What should _{word}_ be tagged?", d="Separate tags with ` @ `.")
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
                entry.tags.extend(tags)
                break

        ndict[word] = entry
        self.save_ndict()
        return await succ.send(self.ctx, f"_{word}_ added.")

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
                await self.emol.send(self.ctx, f"What is the new abbreviated definition of _{word}_?")
                try:
                    abb = await zeph.wait_for("message", check=pred, timeout=600)
                except asyncio.TimeoutError:
                    raise commands.CommandError("Definition timed out.")
                if abb.content.lower() == "cancel":
                    return await self.emol.send(self.ctx, "Edit cancelled.")
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
            await self.ctx.send(f"Current definition of {word}:\n`{re.split(' [@=] ', ndict[word].save())[1]}`")
            while True:
                await self.emol.send(self.ctx, f"What is the new full definition of _{word}_?")
                try:
                    dfn = await zeph.wait_for("message", check=pred, timeout=600)
                except asyncio.TimeoutError:
                    raise commands.CommandError("Definition timed out.")
                if dfn.content.lower() == "cancel":
                    return await self.emol.send(self.ctx, "Edit cancelled.")
                entry = Entry.from_str(f"{ndict[word].abbrev} = {dfn.content}")
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
                await self.emol.send(self.ctx, f"What should _{word}_ be tagged?", d="Separate tags with ` @ `.")
                try:
                    tag = await zeph.wait_for("message", check=pred, timeout=600)
                except asyncio.TimeoutError:
                    raise commands.CommandError("Tags timed out.")
                if tag.content.lower() == "cancel":
                    return await self.emol.send(self.ctx, "Edit cancelled.")
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

    async def _move(self, *args):
        admin_check(self.ctx)

        if len(args) < 2:
            raise commands.CommandError("Format: `z!nd move <from> <to>`")

        if ascii_narahlena(args[0]) not in ndict:
            raise commands.CommandError(f"_{ascii_narahlena(args[0])}_ is not defined.")

        ndict[ascii_narahlena(args[1])] = ndict.pop(ascii_narahlena(args[0]))
        self.save_ndict()
        return await succ.send(self.ctx, f"_{ascii_narahlena(args[0])}_ moved to _{ascii_narahlena(args[1])}_.")

    async def _remove(self, *args):
        admin_check(self.ctx)

        if not args:
            raise commands.CommandError("Format: `z!nd remove <word>`")

        if ascii_narahlena(args[0]) not in ndict:
            raise commands.CommandError(f"_{ascii_narahlena(args[0])}_ is not defined.")

        word = ascii_narahlena(args[0])
        try:
            assert await confirm(
                f"You want to delete the word _{word}_?", self.ctx, add_info=str(ndict[word]) + "\n\n"
            )
        except AssertionError:
            return await self.emol.send(self.ctx, "Removal cancelled.")
        del ndict[word]
        self.save_ndict()
        return await succ.send(self.ctx, f"_{word}_ removed.")

    async def _download(self, *args):
        admin_check(self.ctx)
        return await self.ctx.send(file=discord.File("storage/ndict.txt"))

    async def _markov(self, *args):
        try:
            syls = int(args[0])
        except ValueError:
            raise commands.CommandError("Format: `z!nd markov [syllables]`")
        except IndexError:
            syls = 3

        cons = "bcçčdfghjklmnňprsštvwyzž"
        vows = "aāâeioôu"
        all_syllables = " ".join([
            g for word in [re.split(r"((?=["+cons+"]["+vows+"]))|((?<=["+vows+"])(?=["+vows+"]))", j) for j in ndict]
            for g in word if g
        ]).lower() + " "
        chances = {g: {} for g in cons + vows + " "}
        for ind, char in list(enumerate(all_syllables))[:-1]:
            chances[char][all_syllables[ind + 1]] = chances[char].get(all_syllables[ind + 1], 0) + 1

        ret = ""
        for syl in range(syls):
            onset = choices(list(chances[" "]), weights=list(chances[" "].values()))[0]
            if onset in vows:
                nucleus, onset = onset, ""
            else:
                possible_nuclei = {g: j for g, j in chances[onset].items() if g != " "}
                nucleus = choices(list(possible_nuclei), weights=list(possible_nuclei.values()))[0]
            coda = choices(list(chances[nucleus]), weights=list(chances[nucleus].values()))[0]
            ret += (onset + nucleus + coda).strip()

        return await self.ctx.send(ret.strip())


with open("storage/ndict.txt", "r", encoding="utf-8") as fp:
    ndict_temp = [re.split(r" = ", g, 1) for g in fp.readlines()]
    ndict = {g[0]: Entry.from_str(g[1].strip("\n")) for g in ndict_temp}
    ndict_corp = {
        g: re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9\s]", "", j.save()).lower()).split() for g, j in ndict.items()
    }


@zeph.command(
    name="ndict", aliases=["nd"], usage="z!ndict help",
    description="Accesses the Narahlena dictionary.",
    help="Browses, searches, and (if you're Fort) edits the Narahlena dictionary. Use `z!nd help` for more info."
)
async def ndict_command(ctx: commands.Context, func: str = None, *args: str):
    if not func:
        return await NarahlInterpreter.emol.send(
            ctx, "The Narahlena Dictionary",
            d="Within this command is contained the full lexicon of the Narahlena language. Use `z!nd help` for "
              "the various commands you can use to browse it."
        )
    return await NarahlInterpreter(ctx).run(str(func).lower(), *args)
