from classes.bot import Zeph
from classes.menus import Navigator, scroll_list
from discord.ext import commands
from functions import plural

import pokemon.tcgp as tp


class CardSearchNavigator(Navigator):
    def __init__(self, bot: Zeph, query: str | tp.CardSearchQuery, cards: list[tp.Card]):
        super().__init__(bot, bot.ball_emol("poke"), cards, per=1, prev="🔼", nxt="🔽")
        self.query = query
        self.mode = "search"
        self.funcs[self.bot.emojis["search"]] = self.switch_mode

    def switch_mode(self):
        self.mode = "view" if self.mode == "search" else "search"

    @property
    def name_table(self):
        return [f"{g.id} {g.name} ({tp.expansion_names[g.expansion]})" for g in self.table]

    @property
    def selected_card(self) -> tp.Card:
        return self.table[self.page - 1]

    def con(self):
        if self.mode == "search":
            return self.emol.con(
                f"Cards matching `{str(self.query)}`",
                d=f"{len(self.table)} {plural('match', len(self.table), suffix='es')} found. "
                  f"Press {self.bot.emojis['search']} to view a card in detail.\n\n"
                  f"{scroll_list(self.name_table, self.page - 1, wrap=False)}",
                thumb=self.selected_card.image_url
            )
        else:
            return self.bot.display_card(self.selected_card)


class TCGPocketCog(commands.Cog):
    def __init__(self, bot: Zeph):
        self.bot = bot

    @commands.command(
        name="tcgp", aliases=["tp", "pt"], usage="z!tcgp <card...>",
        description="Shows info about Pok\u00e9mon TCG Pocket cards.",
        help="Shows info about a given Pok\u00e9mon TCG Pocket card, including type, HP, moves, etc. If multiple "
             "cards match the search term, this command instead returns a browsable list of cards. You can search by "
             "name (e.g. `scolipede`), ID (e.g. `A1a-006`), or expansion (e.g. `vaporeon genetic apex`). To include "
             "variants such as full art cards, add `variant` (or `v`, or `var`) to the front of the search term (e.g. "
             "`variant mew ex`)."
    )
    async def tcgp_command(self, ctx: commands.Context, *, text: str):
        if text.lower().split()[0] in ("s", "search"):
            if len(text.split()) == 1:
                return await self.bot.ball_emol("poke").send(
                    ctx, "Card Search",
                    d="Search for cards by specific attributes. Include any combination of the below search terms in "
                      "your message to filter out cards.\n\n"
                      "- `type=x`: Filters by type. `x` be any of the 10 Pok\u00e9mon card types, `pokemon`, "
                      "`trainer`, `supporter`, `item`, or `tool`.\n"
                      "- `stage=x`: Filters by evolution stage. `x` can be `basic`, `1`, or `2`.\n"
                      "- `hp=n`: Filters by HP. You can also use inequalities, such as `hp<50` or `hp>=160`.\n"
                      "- `power=n`: Filters by attack power. Results will only include Pok\u00e9mon with an attack "
                      "whose power is equal to `n`. Moves with variable power are not included. You can also use "
                      "`>`, `>=`, `<`, or `<=`.\n"
                      "- `ex=x`: Filters by ***ex*** status. If `x` is `yes`, `y`, `true`, `t`, or `1`, results will "
                      "only include ***ex*** Pok\u00e9mon. If `x` is `no`, `n`, `false`, `f`, or `0`, results will "
                      "only include non-***ex*** Pok\u00e9mon.\n\n"
                      "Any other arguments passed will be interpreted as plaintext, and results will only match cards "
                      "that contain all those words in their name, description, ability, or attack texts (e.g. `z!pt "
                      "search benched pokemon` will only match cards that contain the words \"benched Pok\u00e9mon\" "
                      "somewhere). You can combine this with other search terms, such as `z!pt search heal type=grass`."
                )
            query = tp.CardSearchQuery.from_str(" ".join(text.split()[1:]))
            matching_cards = query.get_matches()

        else:
            if text.lower().split()[0] in ("v", "var", "variant", "variants") and len(text.split()) > 1:
                query = " ".join(text.split()[1:])
                include_variants = True
            else:
                query = text
                include_variants = False
            matching_cards = tp.name_search(query, include_variants=include_variants)

        if not matching_cards:
            raise commands.CommandError("No cards found matching this search term.")
        elif len(matching_cards) == 1 and not isinstance(query, tp.CardSearchQuery):
            return await ctx.send(embed=self.bot.display_card(matching_cards[0]))
        else:
            return await CardSearchNavigator(self.bot, query, matching_cards).run(ctx)
