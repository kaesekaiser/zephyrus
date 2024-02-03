from epitaph import *
from minigames import planes as pn
from math import sin, cos
import os


async def initialize_planes():
    print("Initializing planes...")
    start = time.time()
    for i in re.findall(pn.pattern, pn.readurl(pn.map_url)):
        pn.City.from_html(i)
    if len(pn.cities) == 0:
        return print("Initialization failed.")
    for i in pn.cities.values():
        if i.country not in pn.countries:
            pn.Country.from_name_only(i.country)
    with open("storage/planes.txt", "r") as read:
        for i in read.readlines():
            us = pn.User.from_str(i)
            zeph.plane_users[us.id] = us
    return print(f"Planes initialized. ({round(time.time() - start, 1)} s)")


@zeph.command(
    aliases=["p"], usage="z!planes help",
    description="A shipping simulator I'm calling Planes.",
    help="Lets you play a game I'm just calling Planes. It's a sort of semi-idle shipping simulator - really similar "
         "to a mobile game called Pocket Planes - where you buy airports and airplanes, and use them to take jobs "
         "back and forth for profit. There's many, many sub-commands, so do `z!planes help` for more info on what "
         "exactly you can do, and how to do it."
)
async def planes(ctx: commands.Context, func: str = None, *args: str):
    if not func:
        return await plane.send(
            ctx, "Planes",
            d="I don't particularly know what this is. If you've ever played Pocket Planes on mobile, it's essentially "
              "that, but a tiny bit different. There's a lot more airports, for one, and there's a distinct lack of a "
              "screen, because it's Discord. I'm working on that. For now though, use `z!planes map` to view all "
              "the airports, and `z!planes help` to view all the possible commands.\n\n"
              "Important side note: One in-game hour is equal to one real-life minute. Everything else is to scale."
        )

    return await PlanesInterpreter(ctx).run(str(func).lower(), *args)


class PlanesInterpreter(Interpreter):
    redirects = {
        "offload": "unload", "city": "airport", "airports": "cities",
        "p": "profile", "f": "fleet", "j": "jobs", "l": "load", "g": "launch", "a": "airport", "c": "country",
        "k": "market", "m": "model", "h": "help", "u": "upgrade", "d": "dist", "e": "eta", "s": "search",
        "b": "buy", "o": "buyout", "r": "rename", "x": "specs", "n": "unload", "t": "tutorial", "y": "licenses"
    }

    @property
    def user(self):
        try:
            assert isinstance(zeph.plane_users[self.au.id], pn.User)
            return zeph.plane_users[self.au.id]
        except KeyError:
            return pn.User(0, {}, [], {}, 0)

    @staticmethod
    def form_et(n):  # formats remaining time
        return round(n) if round(n) >= 1 else "<1"

    @staticmethod
    def form_dt(dt: datetime.datetime):  # used to create timer URLs
        return "".join("".join("T".join(str(dt).split()).split("-")).split(":")).split(".")[0]

    @staticmethod
    def fluctuate(x: float):
        return sin(3 * x / 13) + cos(3 * x / 7) - sin(3 * x / 17) * cos(3 * x / 11)

    @staticmethod
    def invalid_city(s: str):
        return f"Invalid city `{s.lower()}`. Did you mean {pn.cities[best_guess(s.lower(), pn.cities)].name}?"

    @staticmethod
    def valid_job(s: str):
        try:
            pn.Job.from_str(s)
        except ValueError:
            return False
        if pn.Job.from_str(s) not in pn.code_city(s[:2]).jobs:
            return False
        return True

    def pretty_city(self, ci: pn.City, flag=False, italicize_unowned=True):
        flag = f":flag_{pn.country_codes[ci.country]}: " if flag else ""
        return flag + (ci.name if (ci.name in self.user.cities or not italicize_unowned) else f"_{ci.name}_")

    def market_price(self, model: Union[str, pn.Model], delta: int = 0):
        if isinstance(model, str):
            model = pn.craft[model.lower()]
        return round(
            model.cost + 0.1 * model.cost *
            self.fluctuate(time.time() // 86400 + delta + 750 * list(pn.craft.keys()).index(model.name.lower()))
        )

    def plane_value(self, craft: pn.Plane):
        return self.market_price(craft.model) + int(10000 * (2 ** sum(craft.upgrades + [1]) - 1))

    def job_pay(self, job: pn.Job):
        if job.destination.country not in self.user.countries:
            return job.pay
        else:
            return round(job.pay * (0.75 + 0.25 * self.user.countries[job.destination.country]))

    def airport_price(self, airport: pn.City):
        if airport.country not in self.user.countries:
            return airport.value
        else:
            return round(airport.value * (1.1 - 0.1 * self.user.countries[airport.country]))

    def plane_dict(self, airplane: pn.Plane):
        loc = {"Location": airplane.path[0].name} if len(airplane.path) == 0 else \
            {"En-route": "→".join(g.name for g in airplane.path.path), "ETA": f"<t:{airplane.arrival}:R>"}
        job = [f"`{g}` [{pn.code_city(g[2:4]).name} Ȼ{self.job_pay(pn.Job.from_str(g))}]" for g in airplane.jobs]
        return {"Model": airplane.model, **loc, "Available Slots": airplane.pass_cap - len(airplane.jobs),
                "Jobs": ", ".join(job) if len(airplane.jobs) > 0 else "none"}

    def next_stop(self, craft: pn.Plane):
        craft.path.iterate(craft.travel(craft.path[0], craft.path[1]))
        jobs_delivered = 0
        payout = 0
        jobs = [g for g in craft.jobs]
        for i in jobs:
            job = pn.Job.from_str(i)
            if job.destination == craft.path[0]:
                craft.unload(i)
                pay = self.job_pay(job)
                self.user.credits += pay
                jobs_delivered += 1
                payout += pay
        return jobs_delivered, payout

    async def arrival_timer(self, craft: pn.Plane):
        jobs_delivered = 0
        payout = 0
        while len(craft.path) > 0:
            await asyncio.sleep(craft.travel(craft.path[0], craft.path[1]))
            status = self.next_stop(craft)
            jobs_delivered += status[0]
            payout += status[1]

        job_str = f"Jobs delivered: **{jobs_delivered}** / Total payout: **Ȼ{pn.addcomm(payout)}**" \
            if jobs_delivered else ""
        return await plane.send(self.ctx, f"{craft.name} arrived at {craft.path[-1].name}!", d=job_str)

    def filter_jobs(self, city: pn.City, fil: callable, exclusion_exceptions: list = (), reload: bool = True):
        tm = time.time()
        reset = tm // 900 * 900
        if tm - city.job_reset >= 900 and (reload or not city.jobs):
            city.rpj()
            city.job_reset = reset
        jobs = [g for g in city.jobs if (g.code not in self.user.jobs or g.code in exclusion_exceptions) and fil(g)]
        jobs = {
            g.code: f"{self.pretty_city(g.destination, True)} (Ȼ{pn.addcomm(self.job_pay(g))})" for g in jobs
        }
        return {
            "job_ids": jobs,
            "footer": f"new jobs <t:{(tm // 900 + 1) * 900}:R>"
        }

    async def launch_plane(self, craft: pn.Plane, *args: str):
        # NOTE: all errors thrown within this function MUST be of the CommandError class for compatibility
        if len(craft.path) != 0:
            raise commands.CommandError("That plane is currently in the air.")
        for arg in args:
            try:
                city = pn.find_city(arg)
            except KeyError:
                raise commands.CommandError(self.invalid_city(arg))
            if city.name not in self.user.cities:
                raise commands.CommandError(f"You don't have the license to {city.name}.")

        if len(args) > 25:
            raise commands.CommandError("Paths can't be longer than 25 stops.")

        args = [pn.find_city(g) for g in args]
        path = [craft.path[0], *args]
        fuel_cost = 0

        for i in range(len(path) - 1):
            if path[i].dist(path[i + 1]) > craft.range:
                raise commands.CommandError(f"{craft.name} can't reach {path[i + 1].name} from {path[i].name}.")
            if path[i] == path[i + 1]:
                if i == 0:
                    raise commands.CommandError(f"{craft.name} is already at {path[i].name}.")
                raise commands.CommandError(f"Can't take off and immediately land back at the same airport.")

            fuel_cost += round(craft.lpk * path[i].dist(path[i + 1]), 2)

        if round(fuel_cost) > self.user.credits:
            raise commands.CommandError("You don't have enough money for fuel.")

        self.user.credits -= round(fuel_cost)
        craft.launch(*args)
        plane.task = zeph.loop.create_task(self.arrival_timer(craft))
        return await plane.send(
            self.ctx, f"{craft.name} will arrive at {craft.path[-1].name} <t:{craft.arrival}:R>.",
            d=f"ETA: <t:{craft.arrival}:t> / Flight time: `{pn.hrmin(round(craft.arrival - time.time()))}` / "
              f"Fuel cost: Ȼ{pn.addcomm(round(fuel_cost))}"
        )

    async def before_run(self, func: str):
        if self.au.id in zeph.plane_users:
            for craft in self.user.planes.values():
                if len(craft.path) > 0:  # messy; should only be called if zeph went down while a plane was in the air
                    while craft.next_eta and craft.next_eta < time.time():
                        self.next_stop(craft)
        else:
            if func not in ["new", "help", "map", "tutorial"]:
                raise commands.CommandError("You haven't started a Planes company yet; try `z!planes new`.")

    async def _help(self, *args):
        help_dict = {
            "new": "`z!planes new` starts a new game.",
            "tutorial": "`z!planes tutorial` links to the tutorial.",
            "map": "`z!planes map` links to the airport map.",
            "profile": "`z!planes profile` shows your country licenses and credit balance.",
            "fleet": "`z!planes fleet` lists your owned planes.\n\n"
                     "`z!planes fleet <plane>` shows specs for a specific plane.\n\n"
                     "`z!planes fleet sell <plane>` sells a plane for 25% of its purchase value, including "
                     "money spent on upgrades.",
            "country": "`z!planes country <country>` shows information for a country.\n\n"
                       "`z!planes country upgrade <country>` upgrades your license in a country. An upgraded license "
                       "increases the payout for jobs headed to that country, and decreases the price of airports in "
                       "that country. Licenses start at level 1, and may be upgraded up to level 9. You can also "
                       "use the shortcut `z!p c u`.",
            "airport": "`z!planes airport <airport>` shows information for an airport. You can use the :mag: button "
                       "to toggle the zoom on the minimap that appears.\n\n"
                       "`z!planes airport sell <airport>` sells the airport for 25% of its purchase value.",
            "model": "`z!planes model <model>` shows specs for a plane model.",
            "dist": "`z!planes dist <from> <to>` returns the distance between two airports.\n\n"
                    "`z!planes dist <airports>` returns the length of a path along multiple airports.",
            "jobs": "`z!planes jobs <airport>` lists available jobs in an airport.\n\n"
                    "`z!planes jobs <airport> all` lists all jobs headed to all airports, "
                    "including those you don't own.\n\n"
                    "`z!planes jobs <airport> to:<city/country>` lists all jobs headed to a given city or country.\n\n"
                    "If you have a plane landed at the airport, you can also use this command to load jobs "
                    "onto it. Say the number of the job you'd like to load in chat (e.g. `2` for the second job "
                    "in the list), and it will automatically be loaded onto the plane. You can load multiple jobs at "
                    "once by separating them with spaces (e.g. `2 3 5 7`). If you have multiple planes "
                    "landed at the airport, use the ✈ button to switch between them.\n\n"
                    "You can also launch planes from the airport whose jobs you're browsing. If you're loading a "
                    "plane, say `launch` in the chat to bring up a dialogue in which you may set its course; or, "
                    "follow the command with a list of destinations (e.g. `launch london paris rome` - the same way "
                    "as `z!p launch`) to launch the plane straightaway.",
            "launch": "`z!planes launch <plane> <airports>` launches a plane along a path. Be sure to "
                      "keep fuel price in mind. The ETA in the launch message links to a countdown timer "
                      "to arrival, and Zephyrus will notify you when it's arrived.\n\n"
                      "You can chain airports using the `launch` command. For example:\n"
                      "`z!planes launch meadowlark washington newyork boston` will tell Meadowlark to "
                      "follow the path from its current location to Washington, then NewYork, then Boston, "
                      "without stopping. Planes will automatically unload jobs along the way.",
            "buy": "`z!planes buy airport <airports>` purchases the given airport(s), provided you have "
                   "enough funds. You can also use the shortcut `z!p b a`.\n\n"
                   "`z!planes buy country <countries>` does the same, but for countries. You can use the shortcut "
                   "`z!p b c`.\n\n"
                   "`z!planes buy plane <model>` buys a new plane of the given model. You can only buy one plane at a"
                   "time, and you can use the shortcut `z!p b p`.",
            "load": "`z!planes load <job codes>` loads jobs onto a plane. The job code is the "
                    "five-letter/number code on the left side of a job list.",
            "unload": "`z!planes unload <plane> <job codes>` unloads jobs from a plane without pay, "
                      "returning it to its original source.",
            "rename": "`z!planes rename <plane> <new name>` renames a plane. Names can only contain "
                      "alphanumeric characters, dashes, and underscores.",
            "market": "`z!planes market` shows prices for all available plane models. Plane prices fluctuate daily; "
                      "the indicator beside the price tells you whether the price for that model increased or "
                      "decreased today.",
            "eta": "`z!planes eta <plane>` links to the timer for a plane's arrival.",
            "search": "`z!planes search [owned | unowned] [criteria...]` is a robust search/sort method for Planes's "
                      "1100-some airports. At some point in the near future, I'll write a more in-depth tutorial. The "
                      "following search parameters can be used:\n\n"
                      "- `owned` (or `o`) / `unowned` (or `u`) restrict the results to only airports you either do or "
                      "don't own. This param must come first if used.\n\n"
                      "- `in:<country>` restricts the results to only airports in a given country. You can use "
                      "multiple `in` params to search in multiple countries.\n\n"
                      "- `in:owned` (or `in:licensed`) is a shorthand for all countries whose license you own. This "
                      "can be combined with other `in` params.\n\n"
                      "- `near:<city>` sorts the results by distance from a given airport. You can use multiple `near` "
                      "params to search near multiple airports; the sorting will be done by the minimum distance to "
                      "an airport in the list.\n\n"
                      "- `near:any` sorts the results by closest distance to any airport you own. `near:any` can't be "
                      "used with any other `near` params. Because the `near` param excludes the airport(s) you input, "
                      "`near:any` also inherently filters out all owned airports. This makes it very useful to find "
                      "new airports to buy.\n\n"
                      "- `priority:<city>` sorts the results by job priority from a given airport. The percentage "
                      "indicates the approximate proportion of jobs heading to the airport from the parameter.\n\n"
                      "- `sort:name` sorts the results by alphabetical order.\n\n"
                      "- `sort:random` sorts the results randomly.\n\n"
                      "- `startswith:<text>` restricts the results to only airports starting with a given string "
                      "of letters."
                      "\n\nFor example, `z!p s o in:us in:canada near:detroit` returns a list of owned airports in the "
                      "United States or Canada, sorted by distance from Detroit. **All search parameters are "
                      "optional**; `z!p s` returns a list of all airports.",
            "specs": "`z!planes specs <plane>` shows the airspeed, fuel consumption, fuel capacity, and "
                     "upgrade levels for a plane you own.",
            "upgrade": "`z!planes upgrade <plane> <stat>` allows you to upgrade a plane. Upgrades cost Ȼ20,000 "
                       "initially, but each subsequent upgrade is twice as expensive as the last.\n\n"
                       "`z!planes upgrade <plane> power` increases a plane's airspeed by 25%, but also "
                       "increases its fuel consumption by 25%, so its range is not affected.\n\n"
                       "`z!planes upgrade <plane> tank` increases a plane's fuel capacity by 25%, which "
                       "increases its range but does not affect its airspeed or fuel consumption.",
            "buyout": "`z!planes buyout <country>` buys as many airports in a certain country as you can afford, "
                      "starting with the biggest airports. For your personal convenience, so that you can quickly "
                      "expand into a new market without having to manually buy a ton of airports.\n\n"
                      "`z!planes buyout <country> <number>` does the same, but will only buy, at most, `<number>` "
                      "airports.",
            # "ownmap": "`z!planes ownmap` generates + links an image showing every airport you own on a map. It does "
            #           "not yet show names, unfortunately. The technology will get there eventually.",
            "licenses": "`z!planes licenses` lists your owned flight licenses, their levels, and how many airports "
                        "you own in their countries."
        }
        desc_dict = {
            "new": "Starts a brand new game.",
            "tutorial": "Links to the tutorial.",
            "map": "Links to the airport map.",
            "profile": "Shows basic airline data, including credit balance.",
            "fleet": "List or show details for your planes.",
            "country": "Shows info for a country.",
            "airport": "Shows info for an airport.",
            "model": "Shows specs for a plane model.",
            "dist": "Shows distance between two airports, or along a path.",
            "jobs": "Lists available jobs at an airport.",
            "launch": "Launches a plane along a path.",
            "buy": "Buys airports, countries, or planes.",
            "load": "Loads jobs on a plane.",
            "unload": "Removes jobs from a plane.",
            "rename": "Renames a plane.",
            "market": "Browses the market for new planes.",
            "eta": "Shows ETAs for planes.",
            "search": "Searches and sorts airports.",
            "specs": "Shows specs and upgrades for a plane.",
            "upgrade": "Upgrades a plane's engine or fuel tank.",
            "buyout": "Buys all unowned airports in a country you can afford.",
            # "ownmap": "Shows every airport you own on a map.",
            "licenses": "Lists your country licenses in more detail."
        }
        shortcuts = {j: g for g, j in self.redirects.items() if len(g) == 1}

        def get_command(s: str):
            return f"**`{s}`** (or **`{shortcuts[s]}`**)" if shortcuts.get(s) else f"**`{s}`**"

        if len(args) == 0 or (args[0].lower() not in help_dict and args[0].lower() not in self.redirects):
            return await plane.send(
                self.ctx, "z!planes help",
                d="Available functions:\n\n" + "\n".join(f"{get_command(g)} - {j}" for g, j in desc_dict.items()) +
                "\n\nFor information on how to use these, use `z!planes help <function>`."
            )

        ret = self.redirects.get(args[0].lower(), args[0].lower())

        return await plane.send(self.ctx, f"z!planes {ret}", d=help_dict[ret])

    async def _tutorial(self, *args):  # needs to be able to take args like all other commands
        return await plane.send(self.ctx, "z!Planes Tutorials:", d="1. [The Basics](https://imgur.com/a/3ot7qog)")

    async def _map(self, *args):  # also needs to be able to take args
        return await plane.send(self.ctx, "Purchasable airports:", d=pn.map_url)

    async def _profile(self, *args):  # I am once again asking to take args
        airline_value = sum(
            [pn.find_city(g).value for g in self.user.cities] +
            [self.plane_value(g) for g in self.user.planes.values()]
        )

        nat_counts = {nat: len([g for g in pn.cities.values() if g.country == nat]) for nat in self.user.countries}
        licenses = " ".join(
            f":flag_{pn.country_codes[g]}:" for g, _ in
            sorted(list(self.user.countries.items()), key=lambda c: -(c[1] * 1000 + nat_counts[c[0]]))[:10]
        )
        if len(self.user.countries) > 10:
            licenses += f" *...and {len(self.user.countries) - 10} more*"

        return await plane.send(
            self.ctx, f"{self.au.display_name}'s Profile", same_line=True,
            fs={"Licenses": NewLine(licenses),
                "Credits": f"Ȼ{pn.addcomm(self.user.credits)}",
                "Airports": len(self.user.cities),
                "Airline Value": f"Ȼ{pn.addcomm(airline_value)}"}
        )

    async def _fleet(self, *args):
        if len(args) == 0:
            return await plane.send(
                self.ctx, f"{self.au.display_name}'s Fleet",
                fs={p.name: p.fleet_str for p in self.user.planes.values()}, same_line=True
            )

        if args[0] == "sell":
            if len(args) == 1:
                raise commands.CommandError("Format: `z!p fleet sell <plane>`")
            args = args[1], args[0]
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("No owned plane by that name.")

        craft = self.user.planes[args[0].lower()]

        if len(args) > 1 and args[1] == "sell":
            if len(self.user.planes) == 1:
                raise commands.CommandError("You can't sell your last plane.")

            resale = int(self.market_price(craft.model) / 4)
            if await confirm(f"You're selling {craft.name} for Ȼ{pn.addcomm(resale)}.", self.ctx, self.au):
                self.user.planes = \
                    {i: g for i, g in self.user.planes.items() if g.name != craft.name}
                self.user.credits += resale
                return await succ.send(self.ctx, "Plane sold.")

            return await plane.send(self.ctx, "Sale cancelled.")

        return await plane.send(self.ctx, craft.name, fs=self.plane_dict(craft), same_line=True)

    async def _specs(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Format: `z!p specs <plane>`")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("No owned plane by that name.")

        craft = self.user.planes[args[0].lower()]
        return await plane.send(self.ctx, f"{craft.name} ({craft.model})", fs=craft.stats, same_line=True)

    async def _country(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Format: `z!p country <country>`")

        if args[0] in ["upgrade", "u", "--u"]:
            if len(args) == 1:
                raise commands.CommandError("Format: `z!p country upgrade <country>`")
            args = args[1], args[0]

        try:
            country = pn.find_country(args[0])
        except KeyError:
            raise commands.CommandError("Invalid country.")

        assert isinstance(country, pn.Country)

        owned = len([g for g in pn.cities.values() if g.country == country.name
                     and g.name in self.user.cities])

        license_level = self.user.countries.get(country.name, 0)

        if len(args) > 1 and args[1] in ["upgrade", "u", "--u"]:
            if country.name not in self.user.countries:
                raise commands.CommandError(f"You must buy the license to {country.name} first.")

            if license_level == 9:
                raise commands.CommandError("Licenses may not be upgraded past level 9.")

            return await LicenseUpgradeNavigator(self, country).run(self.ctx)

        fields = {
            "Traffic": pn.suff(sum([g.passengers for g in country.cities])),
            "Cities": f"{len(country.cities)} ({owned} owned)",
            "License Value": f"Ȼ{pn.addcomm(country.worth)}",
            "Owned": ["No", "Yes"][country.name in self.user.countries],
            "Flag": f":flag_{pn.country_codes[country.name]}:",
            "Code": f"`{pn.country_codes[country.name].upper()}`"
        }
        if country.name in self.user.countries:
            fields["License Level"] = NewLine(
                f"Your license is **Level {license_level}** [{zeph.emojis['ziplv' + str(license_level)]}]. "
                f"Jobs headed for this country are worth **{round(25 * (license_level - 1))}%** more, "
                f"and airports in this country are **{round(10 * (license_level - 1))}%** cheaper.\n\n"
                f"Your license may be upgraded using `z!p country upgrade {country.name}`." if license_level > 1 else
                f"Your license is **Level 1** [{zeph.emojis['ziplv1']}]. "
                f"This provides no additional bonuses. "
                f"Your license may be upgraded using `z!p country upgrade {country.name}`."
            )

        return await plane.send(self.ctx, country.name, same_line=True, fs=fields)

    async def _airport(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Format: `z!p airport [sell] <airport>`")
        if args[0].lower() in ["sell"]:
            if len(args) == 1:
                raise commands.CommandError("No airport input.")
            args = args[1], args[0], *args[2:]

        try:
            city = pn.find_city(args[0])
        except KeyError:
            raise commands.CommandError(self.invalid_city(args[0]))

        assert isinstance(city, pn.City)

        if len(args) > 1 and args[1].lower() == "sell":
            if city.name not in self.user.cities:
                raise commands.CommandError("You don't own that airport.")

            resale = int(self.airport_price(city) / 4)
            if await confirm(f"You're selling {city.name} Airport for Ȼ{pn.addcomm(resale)}.", self.ctx, self.au):
                self.user.credits += resale
                self.user.cities.remove(city.name)
                return await succ.send(self.ctx, "Airport sold!")

            return await plane.send(self.ctx, "Sale cancelled.")

        message = await plane.send(
            self.ctx, city.name + " Airport",
            fs={**city.dict, "Owned": ["No", "Yes"][city.name in self.user.cities]}, same_line=True
        )

        minimaps = {}
        for zoom in [1, 2, 4]:
            if os.path.exists(f"storage/minimaps/{city.name}{zoom}.png"):  # avoid unnecessary image generation
                minimaps[zoom] = await image_url(f"storage/minimaps/{city.name}{zoom}.png")
            else:
                base = zeph.airport_maps[zoom].copy()
                left_bound = max(0, min(city.imageCoords[zoom][0] - 300, 2752 * zoom - 601))
                upper_bound = max(0, min(city.imageCoords[zoom][1] - 300, 1396 * zoom - 601))
                right_bound = left_bound + 600
                lower_bound = upper_bound + 600
                im.merge_down(zeph.airport_icon, base, *city.imageCoords[zoom], center=True)
                base = base.crop((left_bound, upper_bound, right_bound, lower_bound))
                base.save(f"storage/minimaps/{city.name}{zoom}.png")
                minimaps[zoom] = await image_url(f"storage/minimaps/{city.name}{zoom}.png")

        return await AirportNavigator(self, city, message, minimaps).run(self.ctx, False)

    async def _launch(self, *args):
        if len(args) < 2:
            raise commands.CommandError("Format: `z!p launch <plane> <path...>`")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError(f"No owned plane by the name `{args[0]}`.")

        craft, args = self.user.planes[args[0].lower()], args[1:]
        return await self.launch_plane(craft, *args)

    async def _model(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Format: `z!p model <model>`")
        if args[0].lower() not in pn.craft:
            raise commands.CommandError("That's not a valid model.")

        craft = pn.Plane.new(args[0].lower())
        return await plane.send(
            self.ctx, craft.model, d=f"*{pn.craft[craft.model.lower()].desc}*", same_line=True,
            fs={"Airspeed": f"{craft.airspeed} km/hr", "Job Capacity": craft.pass_cap,
                "Fuel Usage": f"{craft.fuel_use} L/hr ({craft.lpk} L/km)",
                "Fuel Tank": f"{craft.fuel_cap} L", "Range": f"{craft.range} km",
                "Manufacturer": pn.craft[craft.model.lower()].maker}
        )

    async def _dist(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Format: `z!p dist <from> <to...>`")

        try:
            pn.find_city(args[0])
        except KeyError:
            raise commands.CommandError(self.invalid_city(args[0]))

        st = 0
        for i in range(1, len(args)):
            try:
                pn.find_city(args[i])
            except KeyError:
                raise commands.CommandError(self.invalid_city(args[i]))

            st += pn.find_city(args[i - 1]).dist(pn.find_city(args[i]))

        return await plane.send(self.ctx, f"{round(st, 2)} km")

    async def _jobs(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Format: `z!p jobs <airport> [filter...]`")
        try:
            city = pn.find_city(args[0])
        except KeyError:
            raise commands.CommandError(self.invalid_city(args[0]))

        tm = time.time()
        if tm - city.job_reset >= 900 or len(city.jobs) == 0:
            city.rpj()  # only rpj city when called

        fil = lambda j: j.destination.name in self.user.cities
        fil_str = "J"
        if len(args) > 1 and args[1].lower() == "all":
            fil = lambda j: True
            fil_str = "All j"
        elif len(args) > 1 and args[1].lower().startswith("to"):
            if len(args[1].split(":")) != 2:
                raise commands.CommandError("Format: `z!p jobs <airport> to:<destination>`")

            dest = args[1].split(":")[1]

            try:
                fil = lambda j: j.destination.country == pn.find_country(dest).name
                fil_str = f"{pn.find_country(dest).name} j"
            except KeyError:
                try:
                    fil = lambda j: j.destination.name == pn.find_city(dest).name
                    fil_str = f"{pn.find_city(dest).name} j"
                except KeyError:
                    raise commands.CommandError("Destination must be a city or country.")
        elif len(args) > 1:
            raise commands.CommandError(f"Unrecognized argument `{args[1]}`.")

        reset = tm // 900 * 900
        if tm - city.job_reset >= 900:
            city.job_reset = reset

        await JobNavigator(
            self, city, fil, fil_str,
            browse_only=nativity_special_case_match(self.ctx, "zip jobs"),
            footer=f"new jobs in {self.form_et(((tm // 900 + 1) * 900 - tm) // 60)} min"
        ).run(self.ctx)

    async def _load(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Format: `z!p load <job codes...>`")

        plane.send(self.ctx, "Warning: This command will soon be merged into `z!p jobs`.")

        jobs = []
        for job in args:  # filters out duplicates while preserving input order
            if job not in jobs:
                jobs.append(job)

        for job in jobs:
            if not self.valid_job(job):
                raise commands.CommandError(f"Invalid job code `{job.upper()}`.")
            if pn.Job.from_str(job).source != pn.Job.from_str(jobs[0]).source:
                raise commands.CommandError("Cannot simultaneously load jobs from different airports.")
            if job.upper() in self.user.jobs:
                p = [g for g in self.user.planes.values() if job.upper() in g.jobs][0]
                raise commands.CommandError(f"You've already loaded {job} onto {p.name}.")

        possible_planes = [
            g for g in self.user.planes.values() if g.landed_at == pn.Job.from_str(jobs[0]).source and not g.is_full
        ]
        if len(possible_planes) == 0:
            raise commands.CommandError(f"You have no empty planes landed at {pn.Job.from_str(jobs[0]).source.name}.")
        elif len(possible_planes) == 1:
            craft = possible_planes[0]
        else:
            await plane.send(
                self.ctx, f"You have multiple planes landed at {pn.Job.from_str(jobs[0]).source.name}.",
                d=f"Do you want to load these jobs onto {grammatical_join([g.name for g in possible_planes], 'or')}?"
            )

            def pred(m: discord.Message):
                return m.author == self.ctx.author and m.channel == self.ctx.channel and m.content.lower() in \
                    [g.name.lower() for g in possible_planes]

            try:
                mess = await zeph.wait_for("message", timeout=90, check=pred)
            except asyncio.TimeoutError:
                raise commands.CommandError(f"{self.ctx.author.name}'s load request timed out.")
            else:
                craft = [g for g in possible_planes if g.name.lower() == mess.content.lower()][0]

        for job in jobs:
            try:
                craft.load(job.upper())
            except ValueError:
                return await succ.send(self.ctx, f"Fully loaded {craft.name} with the first {jobs.index(job)} job(s).")

        return await succ.send(
            self.ctx, f"Job loaded onto {craft.name}." if len(jobs) == 1 else f"Jobs loaded onto {craft.name}.",
            d=f"{craft.name} is now full." if craft.is_full else
              f"{craft.name} has {craft.pass_cap - len(craft.jobs)} empty slots remaining."
        )

    async def _rename(self, *args):
        if len(args) < 2:
            raise commands.CommandError("Format: `z!p rename <plane> <new name>`")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("No owned plane by that name.")

        nam = self.user.planes[args[0].lower()].name
        if [g in pn.plane_name_chars for g in args[1]].count(False) != 0:
            raise commands.CommandError("Plane names can only contain alphanumerics, dashes, and underscores.")
        if args[1].lower() in self.user.planes:
            raise commands.CommandError("You already have a plane with that name.")
        if args[1].lower() == "sell":
            raise commands.CommandError("You can't name a plane that.")

        self.user.rename(nam, args[1])
        return await succ.send(self.ctx, f"{nam} renamed to {args[1]}.")

    async def _unload(self, *args):
        if len(args) < 2:
            raise commands.CommandError("Format: `z!p unload <plane> <job codes...| all>`")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("No owned plane by that name.")

        craft = self.user.planes[args[0].lower()]
        if len(craft.path) != 0:
            raise commands.CommandError("You can't offload jobs in mid-air.\nYou don't have enough parachutes.")

        if args[1].lower() == "all":
            for i in craft.jobs.copy():
                craft.unload(i.upper())
            return await succ.send(self.ctx, "All jobs offloaded.")
        else:
            jobs = args[1:]
        for i in jobs:
            if i.upper() not in craft.jobs:
                raise commands.CommandError(f"Invalid job code `{i.upper()}`.")

        for i in jobs:
            craft.unload(i.upper())
        return await succ.send(self.ctx, f"{plural('Job', len(jobs))} offloaded.")

    async def _market(self, *args):
        prices = {g.name: self.market_price(g) for g in pn.craft.values()}
        yesterday_prices = {g.name: self.market_price(g, -1) for g in pn.craft.values()}
        prices = {
            g: f"Ȼ{pn.addcomm(prices[g])}"
            f"{zeph.emojis['red_tri_up'] if yesterday_prices[g] < prices[g] else zeph.emojis['green_tri_down']}"
            for g in prices
        }
        return await FieldNavigator(
            plane, prices, 6, "The Market [{page}/{pgs}]", same_line=True,
            footer="Use z!p model to see detailed stats, and z!p buy to buy a plane."
        ).run(self.ctx)

    async def _eta(self, *args):
        if len(args) == 0:
            def eta(p: pn.Plane):
                return f"**`LANDED`** at {p.landed_at.name}" if len(p.path) == 0 else \
                    f"**`ARRIVING`** at {p.path[-1].name} <t:{p.arrival}:R>"

            return await plane.send(
                self.ctx, "All ETAs",
                d="\n".join(f"{g.name} - {eta(g)}" for g in self.user.planes.values())
            )
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("No owned plane by that name.")

        craft = self.user.planes[args[0].lower()]
        if len(craft.path) == 0:
            return await plane.send(self.ctx, f"{craft.name} is landed at {craft.path[0].name}.")
        return await plane.send(self.ctx, f"{craft.name} will arrive at {craft.path[-1].name} <t:{craft.arrival}:R>.")

    async def _upgrade(self, *args):
        if len(args) < 2:
            raise commands.CommandError("Format: `z!p upgrade <plane> <tank | power>`")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("No owned plane by that name.")

        craft = self.user.planes[args[0].lower()]
        if len(craft.path) != 0:
            raise commands.CommandError("That plane is currently in the air.")

        ups = ["power", "tank"]
        if args[1].lower() not in ups:
            raise commands.CommandError("Upgrade type must be `tank` or `power`.")

        up_cost = int(10000 * 2 ** sum(craft.upgrades + [1]))
        if up_cost > self.user.credits:
            raise commands.CommandError(
                f"You don't have enough credits. Your next upgrade will cost Ȼ{pn.addcomm(up_cost)}."
            )

        comp_craft = pn.Plane.from_str(str(craft))
        new_grade = [craft.upgrades[0] + (args[1].lower() == "power"),
                     craft.upgrades[1] + (args[1].lower() == "tank")]
        comp_craft.upgrades = new_grade

        if args[1].lower() == "power":
            comparison = f"This will increase its **airspeed** to **{comp_craft.airspeed} km/hr** " \
                f"(from {craft.airspeed} km/hr), and its **fuel usage** to **{comp_craft.fuel_use} L/hr** " \
                f"(from {craft.fuel_use} L/hr).\n\n"
        else:
            comparison = f"This will increase its **fuel capacity** to **{comp_craft.fuel_cap} L** " \
                f"(from {craft.fuel_cap} L), which means its **range** will increase to **{comp_craft.range} km** " \
                f"(from {craft.range} km).\n\n"

        if await confirm(f"Are you sure you want to upgrade {craft.name}'s {args[1].lower()} for "
                         f"Ȼ{pn.addcomm(up_cost)}?", self.ctx, self.au, add_info=comparison):
            self.user.credits -= up_cost
            craft.upgrades = new_grade
            return await succ.send(self.ctx, "Plane upgraded!")
        return await plane.send(self.ctx, "Upgrade cancelled.")

    async def _buyout(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Format: `z!p buyout <country>`")
        try:
            country = pn.find_country(args[0])
        except KeyError:
            raise commands.CommandError(f"Invalid country `{args[0]}`.")

        assert isinstance(country, pn.Country)
        if country.name not in self.user.countries:
            raise commands.CommandError(f"You don't have the license to {country.name}.")

        if len(args) > 1:
            try:
                stop_at = int(args[1])
            except ValueError:
                stop_at = len(country.cities)
        else:
            stop_at = len(country.cities)

        bought, price, total = [], 0, True
        for city in country.cities:
            if sum([self.airport_price(g) for g in bought] + [self.airport_price(city)]) > self.user.credits or \
                    len(bought) == stop_at:
                if not bought:
                    raise commands.CommandError(f"You can't afford the biggest airport in {country.name}.")
                total = False
                break

            if city.name not in self.user.cities:
                bought.append(city)
                price += self.airport_price(city)

        if not bought:
            raise commands.CommandError(f"You already own every airport in {country.name}.")

        confirm_text = "every airport" if total else f"the {len(bought)} biggest airports"
        try:
            assert await confirm(
                f"You're buying {confirm_text} in {country.name} for Ȼ{pn.addcomm(price)}.", self.ctx, self.au
            )
        except AssertionError:
            return await plane.send(self.ctx, "Purchase cancelled.")

        for i in bought:
            self.user.cities.append(i.name)
        self.user.credits -= price
        return await succ.send(self.ctx, f"Airports purchased!")

    async def _restart(self, *args):
        try:
            assert await confirm(
                "`WARNING:` This will completely and absolutely wipe your Planes data.", self.ctx, self.au,
                add_info="All progress will be lost, and you won't be able to get it back, except through your own "
                         "blood, sweat, and tears. Are you sure you want to start over?\n", yes="wipe everything"
            )
        except AssertionError:
            return await plane.send(self.ctx, "Game data not wiped.")
        else:
            mess = await plane.send(self.ctx, "Alright, one moment...")
            await asyncio.sleep(2 + random() * 2)
            del zeph.plane_users[self.au.id]
            return await succ.edit(mess, "Done.", d="Call `z!planes new` to start anew.")

    async def _buy(self, *args):
        if len(args) < 2:
            raise commands.CommandError(
                "Format: `z!p buy <airport | country | plane> <purchases...>`\n"
                "See `z!p help buy` for more details."
            )

        if args[0].lower() in ["a", "airport", "airports", "city", "cities"]:
            purchases = []
            for i in args[1:]:
                try:
                    purchases.append(pn.find_city(i))
                except KeyError:
                    raise commands.CommandError(self.invalid_city(i))

            for i in purchases:
                if i.name in self.user.cities:
                    raise commands.CommandError(f"You already own {i.name}.")
                if i.country not in self.user.countries:
                    raise commands.CommandError(f"You don't have the license to {i.country}.")

            cost = round(sum(self.airport_price(g) for g in purchases))
            if cost > self.user.credits:
                raise commands.CommandError(f"You don't have enough credits; you need Ȼ{add_commas(cost)}.")

            if await confirm(
                f"You're buying {len(purchases)} airport(s) for a total of Ȼ{add_commas(cost)}.", self.ctx, self.au
            ):
                self.user.credits -= cost
                self.user.cities.extend(g.name for g in purchases)
                return await succ.send(self.ctx, "Airport(s) purchased.")

        elif args[0].lower() in ["c", "country", "countries", "license", "licenses"]:
            purchases = []
            for i in args[1:]:
                try:
                    purchases.append(pn.find_country(i))
                except KeyError:
                    raise commands.CommandError(self.invalid_city(i))

            for i in purchases:
                if i.name in self.user.countries:
                    raise commands.CommandError(f"You already own the license to {i.name}.")

            cost = round(sum(g.worth for g in purchases))
            if cost > self.user.credits:
                raise commands.CommandError(f"You don't have enough credits; you need Ȼ{add_commas(cost)}.")

            if await confirm(
                f"You're buying {len(purchases)} country license(s) for a total of Ȼ{add_commas(cost)}.",
                self.ctx, self.au
            ):
                self.user.credits -= cost
                self.user.countries.update([(g.name, 1) for g in purchases])
                return await succ.send(self.ctx, "License(s) purchased.")

        elif args[0].lower() in ["p", "plane", "planes"]:
            if len(args) > 2:
                raise commands.CommandError("Only buy one plane at a time.")

            if args[1].lower() not in pn.craft:
                raise commands.CommandError("Invalid model.")

            model = pn.craft[args[1].lower()]
            price = self.market_price(model)
            if price > self.user.credits:
                raise commands.CommandError("You don't have enough credits.")

            if await confirm(f"You're buying a {model.name} for Ȼ{pn.addcomm(price)}.",
                             self.ctx, self.au):
                await succ.send(self.ctx, "Aircraft purchased! What would you like to name your new craft?")

                def pred1(m: discord.Message):
                    return m.author == self.au and m.channel == self.ctx.channel

                def pred2(m: discord.Message):
                    if m.author == self.au and m.channel == self.ctx.channel:
                        try:
                            pn.find_city(m.content.lower())
                        except KeyError:
                            return False
                        else:
                            return True

                while True:
                    try:
                        mess = await zeph.wait_for("message", timeout=300, check=pred1)
                    except asyncio.TimeoutError:
                        return await plane.send(self.ctx, "Purchase timed out and cancelled.")

                    else:
                        if [g in pn.plane_name_chars for g in mess.content].count(False) != 0:
                            await plane.send(self.ctx,
                                             "Plane names can only contain alphanumerics, dashes, and underscores.",
                                             d=f"What would you like to name your new {model.name}?")
                        elif mess.content.lower() in self.user.planes:
                            await plane.send(self.ctx, "You already own a plane by that name.",
                                             d=f"What would you like to name your new {model.name}?")
                        elif mess.content.lower() == "sell":
                            await plane.send(self.ctx, "You can't name a plane that.",
                                             d=f"What would you like to name your new {model.name}?")
                        else:
                            await succ.send(self.ctx, f"{model.name} named {mess.content}.")
                            new = pn.Plane.new(model.name.lower())
                            new.name = mess.content
                            break

                await plane.send(self.ctx, f"What city do you want to deploy {new.name} in?")
                while True:
                    try:
                        mess = await zeph.wait_for("message", timeout=300, check=pred2)
                    except asyncio.TimeoutError:
                        return await plane.send(self.ctx, "Purchase timed out and cancelled.")

                    else:
                        if pn.find_city(mess.content).name not in self.user.cities:
                            await plane.send(self.ctx, f"You don't own {pn.find_city(mess.content).name}.",
                                             d=f"What city do you want to deploy {new.name} in?")
                        else:
                            new.path = pn.Path(0, pn.find_city(mess.content))
                            self.user.credits -= price
                            self.user.planes[new.name.lower()] = new
                            return await succ.send(self.ctx, f"{new.name} ready for flight!")

            else:
                return await plane.send(self.ctx, "Purchase cancelled.")

    async def _new(self, *args):
        if self.ctx.author.id in zeph.plane_users:
            return await plane.send(
                self.ctx, "You've already started a game, but you can start over using `z!planes restart` if you want."
            )

        def pred(m: discord.Message):
            return m.author == self.au and m.channel == self.ctx.channel and len(m.content.split()) == 1

        await plane.send(
            self.ctx, "Pick any city to start your empire in.",
            d=f"Click [this link](https://imgur.com/a/3ot7qog) to go to the tutorial.\n\n"
              f"Click [this link]({pn.map_url}) to see the full map of available airports. You'll get the license to "
              f"the country along with your first airport. Make sure to omit spaces."
        )
        while True:
            try:
                cho = await zeph.wait_for("message", timeout=300, check=pred)
            except asyncio.TimeoutError:
                return await plane.send(self.ctx, f"{self.au.display_name}'s request timed out.")
            else:
                if cho.content.lower() in pn.cities:
                    cho = cho.content.lower()
                    cit = pn.cities[cho]
                    nam = choice(pn.starter_names)
                    zeph.plane_users[self.au.id] = pn.User(
                        self.au.id, {cit.country: 1}, [cit.name],
                        {nam.lower(): pn.Plane(pn.craft["tyne-647"], nam, pn.Path(0, cit), [], [0, 0])}, 1000000
                    )
                    return await plane.send(
                        self.ctx, f"Great! {pn.cities[cho].name} Airport purchased.",
                        d=f"You've also received the license to {pn.cities[cho].country} and a Tyne-647 to start you "
                        f"out. To learn how to play, use `z!p tutorial`. Have at it!"
                    )
                await plane.send(self.ctx, "That's not a recognized city.")

    async def _search(self, *args):
        return await AirportSearchNavigator(self, *[g.lower() for g in args]).run(self.ctx)

#     async def _ownmap(self, *args):
#         message = await Emol(zeph.emojis["loading"], hexcol("66757F")).send(self.ctx, "Generating...")
#
#         base = zeph.airport_maps[4].copy()
#         icon = im.Image.open("minigames/minimaps/airport.png").convert("RGBA")
#
#         for city in pn.cities.values():
#             if city.name in self.user.cities:
#                 im.merge_down(icon, base, *city.imageCoords[4], center=True)
#
#         base.save("storage/ownmap.png")
#         return await plane.edit(
#             message, "Owned Airports",
#             image=(await image_url("storage/ownmap.png")), footer="Click to open full image."
#         )

    async def _admin(self, *args):
        admin_check(self.ctx)

        if len(args) < 1:
            raise commands.CommandError("Format: `z!p admin <function> <args...>`")

        if args[0] in ["funds", "credits", "gold", "$"]:
            if len(args) < 2:
                raise commands.CommandError("Format: `z!p admin credits <#>`")
            if not can_int(args[1]):
                raise commands.CommandError("Format: `z!p admin credits <#>`")

            if len(args) > 2 and can_int(args[2]):
                try:
                    user = zeph.plane_users[int(args[2])]
                except KeyError:
                    raise commands.CommandError("User ID not found.")
            else:
                user = self.user

            user.credits += int(args[1])

            return await succ.send(
                self.ctx,
                f"Credits changed by {'-' if int(args[1]) < 0 else ''}Ȼ{pn.addcomm(abs(int(args[1])))}.",
                d=f"New value: **Ȼ{pn.addcomm(user.credits)}**."
            )

        if args[0] in ["cache", "clearcache", "clear_cache"]:
            tm = time.time()
            for city in pn.cities.values():
                if city.jobs and city.job_reset < tm - 3600:  # if a city hasn't been checked in the last hour
                    city.jobs.clear()
            return await succ.send(self.ctx, "Job cache cleared.")

    async def _licenses(self, *args):
        nat_counts = {nat: len([g for g in pn.cities.values() if g.country == nat]) for nat in self.user.countries}
        licenses = [
            f":flag_{pn.country_codes[k]}: **{k}**: Level {v} [{zeph.emojis['ziplv' + str(v)]}]\n"
            f"- {len([g for g in self.user.cities if pn.city_countries[g] == k])}/{nat_counts[k]} airports owned"
            for k, v in sorted(list(self.user.countries.items()), key=lambda c: -(c[1] * 1000 + nat_counts[c[0]]))
        ]
        return await Navigator(plane, licenses, 4, "Flight Licenses [{page}/{pgs}]").run(self.ctx)


class JobNavigator(NumSelector):
    launch_commands = ["launch", "go", "g"]

    def __init__(self, inter: PlanesInterpreter, city: pn.City, fil: callable, fil_str: str, **kwargs):
        super().__init__(plane, s=f"{fil_str}obs in {city.name}" + " [{page}/{pgs}]", timeout=180, multi=True, **kwargs)
        self.interpreter = inter
        self.city = city
        self.filter = fil
        self.is_browse_only = kwargs.pop("browse_only", False)
        if self.available_planes:
            self.plane = list(self.available_planes.values())[0]
        else:
            self.plane = None
        self.mode = "terminal"
        self.all_jobs = {}  # keys are IDs, values are display strings; output of PlanesInterpreter.filter_jobs()
        self.update_jobs()
        self.funcs["🔄"] = self.update_jobs
        self.funcs["✈"] = self.switch_planes
        self.funcs[zeph.emojis["no"]] = self.close
        self.funcs["exit"] = self.close

        self.nativity = Nativity(self.ctx, special_case="zip jobs")
        if not self.is_browse_only:
            self.activate_nativity()

    @property
    def pgs(self):
        return (len(self.all_jobs) - 1) // self.per + 1

    @property
    def ctx(self):
        return self.interpreter.ctx

    @property
    def available_planes(self):
        if self.is_browse_only:
            return {}
        ret = {g.name: g for g in self.interpreter.user.planes.values() if g.landed_at == self.city}
        if not ret:
            self.plane = None
        return ret

    @property
    def loaded_jobs(self):
        if not self.plane:
            return []
        return self.plane.jobs

    @property
    def page_list(self):
        return page_list(list(self.all_jobs.items()), self.per, self.page)

    def update_jobs(self, reload: bool = True):
        self.check_plane()
        self.page = 1
        ret = self.interpreter.filter_jobs(self.city, self.filter, self.loaded_jobs, reload=reload)
        self.all_jobs = ret["job_ids"]
        self.kwargs["footer"] = ret["footer"]

    def check_plane(self):
        if self.plane not in self.available_planes.values():  # works if self.plane is None, which also won't be there
            return self.reset_loading_plane()

    def switch_planes(self):
        if self.mode == "terminal":
            if self.is_browse_only:
                if not nativity_special_case_match(self.ctx, "zip jobs"):
                    self.activate_nativity()
            self.check_plane()
            self.mode = "hangar"
        elif self.mode == "hangar":
            self.update_jobs(reload=False)
            self.mode = "terminal"

    def activate_nativity(self):
        self.is_browse_only = False
        zeph.nativities.append(self.nativity)

    def reset_loading_plane(self):
        try:
            self.plane = list(self.available_planes.values())[0]
        except IndexError:
            self.plane = None

    async def close(self):
        self.closed_elsewhere = True
        try:
            zeph.nativities.remove(self.nativity)
        except ValueError:
            pass
        return await self.remove_buttons()

    def advance_page(self, direction: int):
        if self.mode == "terminal":
            self.page = (self.page + direction - 1) % self.pgs + 1
        elif self.mode == "hangar":
            available_planes = self.available_planes  # preallocate for speed
            if not available_planes:
                return
            else:
                try:
                    pos = (list(available_planes.keys()).index(self.plane.name) + direction) % len(available_planes)
                except ValueError:
                    self.reset_loading_plane()
                else:
                    self.plane = list(available_planes.values())[pos]

    def is_valid_nonnumerical_input(self, s: str):
        return s.split()[0].lower() in self.launch_commands or s.lower() == "exit"

    async def run_nonnumerical_input(self, user_input: str, ctx: commands.Context):
        if user_input.split()[0].lower() in self.launch_commands:
            return await self.launch_protocol(*user_input.split()[1:])

    def select(self, job_no: int):
        if not self.plane:
            return
        if self.plane.landed_at != self.city:
            self.reset_loading_plane()
            return
        try:
            job = page_list(list(self.all_jobs.keys()), self.per, self.page)[job_no]
        except IndexError:
            return
        if job in self.plane.jobs:
            self.plane.unload(job)
        else:
            if self.plane.is_full:
                return
            else:
                self.plane.load(job)

    async def launch_protocol(self, *path: str):
        self.check_plane()
        if not self.plane:
            return

        async def exit_message(message: discord.Message, text: str):
            await plane.edit(message, text)
            await asyncio.sleep(4)
            await message.delete()

        if not path:
            if self.plane.jobs:
                sorted_cities = sorted(
                    set(pn.Job.from_str(g).destination.name for g in self.plane.jobs),
                    key=lambda c: self.city.dist(pn.cities[c.lower()])
                )
                job_appendix = f"\n\n{self.plane.name} is carrying jobs bound for " \
                    f"{grammatical_join(sorted_cities)}."
            else:
                job_appendix = ""

            prompt_title = f"What destinations should {self.plane.name} fly to?"
            prompt_desc = "Say them all in order, separated by spaces, or say `cancel` to cancel." + job_appendix

            def pred(m: discord.Message):
                return m.channel == self.ctx.channel and m.author == self.interpreter.au

            mess = await plane.send(self.ctx, prompt_title, d=prompt_desc)

            while True:
                try:
                    response = await zeph.wait_for("message", check=pred, timeout=60)
                except asyncio.TimeoutError:
                    return await exit_message(mess, "Launch timed out. Returning to main jobs menu.")

                response_text = response.content.lower()
                await response.delete()

                if response_text == "cancel":
                    return await exit_message(mess, "Returning to main jobs menu.")

                try:
                    await self.interpreter.launch_plane(self.plane, *response_text.split())
                except commands.CommandError as e:
                    await plane.edit(mess, str(e))
                    await asyncio.sleep(5)
                    await plane.edit(mess, prompt_title, d=prompt_desc)
                else:
                    if self.available_planes:
                        self.reset_loading_plane()
                        self.update_jobs(reload=False)
                        return await exit_message(mess, "Returning to main jobs menu.")
                    else:
                        return await self.close()

        else:
            try:
                await self.interpreter.launch_plane(self.plane, *path)
            except commands.CommandError as e:
                mess = await plane.send(self.ctx, str(e))
                await asyncio.sleep(5)
                await mess.delete()
            else:
                if self.available_planes:
                    self.reset_loading_plane()
                    self.update_jobs(reload=False)
                    mess = await plane.send(self.ctx, "Returning to main jobs menu.")
                    await asyncio.sleep(2)
                    return await mess.delete()
                else:
                    return await self.close()

    def con(self):
        if self.mode == "terminal":
            if not self.all_jobs:
                prefix = ""
            elif self.is_browse_only:
                prefix = "This list is in **browse-only mode**. Hit ✈ for more info."
            elif not self.available_planes:
                prefix = f"You have no planes at this city to load jobs onto."
            else:
                prefix = f"You are currently loading jobs onto **{self.plane.name}**. " \
                    f"This plane has **{self.plane.pass_cap - len(self.plane.jobs)}** available cargo slots."
                if len(self.available_planes) > 1:
                    prefix += " Hit the ✈ button to switch loading planes."

            display_table = none_list(
                [f"**`[{n+1}]`** {g[1]} {'📦' if g[0] in self.loaded_jobs else ''}"
                 for n, g in enumerate(self.page_list)], joiner="\n"
            )

            appendix = f"\nNew jobs available <t:{round(self.city.job_reset + 900)}:R>.\n\n"
            if time.time() > self.city.job_reset + 900:
                appendix = "\n:sparkles: **New jobs available!** Hit 🔄 to refresh.\n\n"

            return plane.con(
                self.title.format(page=self.page, pgs=self.pgs),
                d=prefix + appendix + display_table,
                footer="Enter the number beside a job to load or unload it.\n"
                       "You can also load multiple at once, e.g. \"123\" or \"3 6 8\".\n"
                       "To depart, enter \"go\" followed by a city or path, e.g. \"go london paris berlin\"."
                       if prefix.startswith("You are") else None
            )

        elif self.mode == "hangar":
            available_planes = self.available_planes  # preallocate for speed

            if self.is_browse_only:
                return plane.con(
                    f"Planes landed at {self.city.name}",
                    d=f"This list is in **browse-only mode** to prevent interference with another open jobs menu. "
                      f"If you want to load jobs at this airport, first close the other menu with "
                      f"{zeph.emojis['no']}, then return to this one."
                )

            if not available_planes:
                title_suffix = ""
                desc = "*none*"
            else:
                if self.plane not in available_planes.values():
                    self.reset_loading_plane()

                pos = list(available_planes.keys()).index(self.plane.name)

                if len(available_planes) > 8:
                    page = pos // 8 + 1
                    title_suffix = f" [{page}/{len(available_planes) // 8 + 1}]"
                else:
                    page = 1
                    title_suffix = ""

                plane_list = [
                    f"- *{k}* ({v.pass_cap - len(v.jobs)} available slots)" for k, v in self.available_planes.items()
                ]
                desc = none_list(page_list(
                    [f"**{g}**" if n == pos else g for n, g in enumerate(plane_list)], 8, page
                ), "\n")

            return plane.con(f"Planes landed at {self.city.name}" + title_suffix, d=desc)

        else:
            return err.con("Something has gone horribly wrong.")


class AirportNavigator(Navigator):
    def __init__(self, inter: PlanesInterpreter, city: pn.City, message: discord.Message, minimaps: dict):
        super().__init__(plane, title=f"{city.name} Airport", prev="", nxt="")
        self.interpreter = inter
        self.city = city
        self.funcs["🔍"] = self.zoom
        self.zoom_level = 2
        self.message = message
        self.minimaps = minimaps

    def zoom(self):
        self.zoom_level = {1: 2, 2: 4, 4: 1}[self.zoom_level]

    def con(self):
        return self.emol.con(
            self.city.name + " Airport", same_line=True,
            fs={**self.city.dict, "Owned": ["No", "Yes"][self.city.name in self.interpreter.user.cities]},
            thumb=self.minimaps[self.zoom_level]
        )


class AirportSearchNavigator(Navigator):
    def __init__(self, inter: PlanesInterpreter, *args):
        super().__init__(plane, [], 5, "Airport Search [{page}/{pgs}]", prev="", nxt="", timeout=120)
        self.interpreter = inter
        self.funcs["⏪"] = self.back_five
        self.funcs["◀"] = self.back_one
        self.funcs["▶"] = self.forward_one
        self.funcs["⏩"] = self.forward_five

        if args:
            self.own = {"o": "owned", "u": "unowned"}.get(args[0], args[0])
            if self.own not in ["owned", "unowned"]:
                self.own = "all"
            else:
                args = args[1:]
        else:
            self.own = "all"

        if any(g[-1] == ":" for g in args):
            raise commands.CommandError(
                "Don't put spaces between the sort parameters and their values.\n"
                "i.e. do `near:london`, not `near: london` or `near london`."
            )

        self.criteria = self.read_criteria(" " + " ".join(args))
        self.countries = self.criteria["in"] if self.criteria["in"] else [g.name for g in pn.countries.values()]

        if self.criteria["near"] == "any":
            self.sort = lambda x: min([x.dist(pn.find_city(g)) for g in self.interpreter.user.cities])
        elif self.criteria["near"]:
            self.sort = lambda x: min([x.dist(g) for g in self.criteria["near"]])
        elif self.criteria["priority"]:
            if self.criteria["priority"] == "any":
                raise commands.CommandError("You can only sort by job priority from one airport.")
            try:
                self.sort = lambda x: -pn.priority(self.criteria["priority"], x)
            except KeyError:
                raise commands.CommandError(f"Unrecognized airport `{self.criteria['priority']}`.")
        elif self.criteria["sort"] == "name":
            self.sort = lambda x: x.name
        elif self.criteria["sort"] == "random":
            self.sort = lambda x: random()
        else:
            self.sort = lambda x: -x.passengers

        table = sorted(
            (g for g in pn.cities.values() if (self.criteria["near"] != "any" and g not in self.criteria["near"]) or
             (self.criteria["near"] == "any" and g.name not in self.interpreter.user.cities)),
            key=self.sort
        )

        if self.criteria["priority"]:
            self.total_priority = sum(2 ** pn.priority(self.criteria["priority"], g) for g in pn.cities.values())
            if any(not self.check_city(g) for g in table):
                filter_priority = sum(
                    2 ** pn.priority(self.criteria['priority'], g) for g in table if self.check_city(g)
                )
                self.kwargs["footer"] = f"total priority: {round(filter_priority / self.total_priority * 100, 3)}%"
        else:
            self.total_priority = 0

        self.table = [self.form_city(g) for g in table if self.check_city(g)]

    def back_five(self):
        self.advance_page(-5)

    def back_one(self):
        self.advance_page(-1)

    def forward_one(self):
        self.advance_page(1)

    def forward_five(self):
        self.advance_page(5)

    def check_city(self, city: pn.City):
        if self.own == "owned":
            if city.name not in self.interpreter.user.cities:
                return False
        elif self.own == "unowned":
            if city.name in self.interpreter.user.cities:
                return False
        if self.criteria["startswith"]:
            if not city.name.lower().startswith(self.criteria["startswith"]):
                return False
        if self.criteria["priority"]:
            if pn.priority(self.criteria["priority"], city) < 0:
                return False
        return city.country in self.countries

    def form_city(self, city: pn.City):
        if self.criteria["near"] == "any":
            nearest = sorted([pn.find_city(g) for g in self.interpreter.user.cities], key=lambda x: x.dist(city))[0]
            dist = f" / {round(nearest.dist(city))} km from {nearest.name}"
        elif self.criteria["near"]:
            nearest = sorted(self.criteria["near"], key=lambda x: x.dist(city))[0]
            if len(self.criteria["near"]) == 1:
                dist = f" / {round(nearest.dist(city))} km"
            else:
                dist = f" / {round(nearest.dist(city))} km from {nearest.name}"
        elif self.criteria["priority"]:
            dist = f" / {round(100 * (2 ** pn.priority(self.criteria['priority'], city)) / self.total_priority, 3)}%"
        else:
            dist = ""
        cost = f"Ȼ{pn.addcomm(self.interpreter.airport_price(city))}" if city.name not in self.interpreter.user.cities \
            else "owned"
        return f"**{self.interpreter.pretty_city(city, True, False)}**\n- {pn.suff(city.passengers)} / {cost}{dist}"

    def read_criteria(self, args: str):
        possible_params = ["in", "near", "sort", "startswith", "priority"]
        sorting_params = ["near", "sort", "priority"]
        ret = {g: re.findall(r"(?<=\s"+g+r":).+?(?=\s|$)", args) for g in possible_params}

        additional_countries = []
        for i in ret["in"]:
            try:
                pn.find_country(i)
            except KeyError:
                if i in ["license", "licensed", "own", "owned"]:
                    additional_countries.extend(list(self.interpreter.user.countries.keys()))
                else:
                    raise commands.CommandError(f"Invalid country `{i}`.")
        ret["in"] = list(set(
            [pn.find_country(g).name for g in ret["in"] if g not in ["license", "licensed", "own", "owned"]] +
            additional_countries
        ))

        if [bool(ret[g]) for g in sorting_params].count(True) > 1:
            raise commands.CommandError("Cannot combine multiple sorting params.")

        if "any" in ret["near"]:
            if len(ret["near"]) > 1:
                raise commands.CommandError("Cannot combine other `near` params with `near:any`.")
            ret["near"] = "any"
        else:
            for i in ret["near"]:
                try:
                    pn.find_city(i)
                except KeyError:
                    raise commands.CommandError(f"Invalid airport `{i}`.")
            ret["near"] = [pn.find_city(g) for g in ret["near"]]

        if len(ret["priority"]) > 1:
            raise commands.CommandError("Cannot use more than one `priority` param.")
        elif ret["priority"]:
            try:
                ret["priority"] = pn.find_city(ret["priority"][0])
            except KeyError:
                raise commands.CommandError("`priority` param must be an airport.")

        if len(ret["sort"]) > 1:
            raise commands.CommandError("Cannot use more than one `sort` param.")
        elif ret["sort"]:
            ret["sort"] = ret["sort"][0]
            possible_sorts = ["name", "random"]
            if ret["sort"] not in possible_sorts:
                raise commands.CommandError(f"`sort` param must be one of `{' '.join(possible_sorts)}`.")

        if len(ret["startswith"]) > 1:
            raise commands.CommandError("Cannot use more than one `startswith` param.")
        elif ret["startswith"]:
            ret["startswith"] = ret["startswith"][0]

        return ret


class LicenseUpgradeNavigator(Navigator):
    def __init__(self, inter: PlanesInterpreter, country: pn.Country):
        super().__init__(plane, list(range(1, 10)), 1, f"{country.name} License Upgrades", timeout=180)
        self.interpreter = inter
        self.country = country
        self.current_level = self.interpreter.user.countries[country.name]
        self.page = self.current_level
        self.funcs[zeph.emojis["yes"]] = self.purchase_upgrade
        self.funcs[zeph.emojis["no"]] = self.close

    async def purchase_upgrade(self):
        if self.current_level >= self.page:
            return

        price = self.country.upgrade_price(self.page, self.current_level)

        if price <= self.interpreter.user.credits:
            self.interpreter.user.credits -= price
            self.interpreter.user.countries[self.country.name] = self.page
            await succ.send(self.interpreter.ctx, f"Level {self.page} license purchased.")
            return await self.close()
        else:
            return

    async def close(self):
        self.closed_elsewhere = True
        await plane.edit(self.message, "This menu has closed.")
        await self.remove_buttons()

    def con(self):
        desc = f"**License Level {self.page} [{zeph.emojis['ziplv' + str(self.page)]}]:**\n" \
            f"Job payout boost: **+{round(25 * (self.page - 1))}%**\n" \
            f"Airport price: **-{round(10 * (self.page - 1))}%**"

        price = self.country.upgrade_price(self.page, self.current_level)

        if self.current_level > self.page:
            desc += f"\n\nYou already have a higher-level license. Your license is Level {self.current_level}."
        elif self.current_level == self.page:
            desc += "\n\nThis is your current license level."
        else:
            desc += f"\n\nUpgrading to this level will cost **Ȼ{pn.addcomm(price)}**.\n"
            if price <= self.interpreter.user.credits:
                desc += f"Hit the {zeph.emojis['yes']} button to confirm upgrade."
            else:
                desc += "You do not have enough credits for this upgrade."

        return plane.con(self.title, d=desc)
