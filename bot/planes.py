from rpg import *


@client.command(pass_context=True, aliases=["p"])
async def planes(ctx: Context, func=None, *args):
    if func is None:
        return await planesay("Planes",
                              d="I don't particularly know what this is. If you've ever played Pocket Planes on mobile,"
                                " it's essentially that, but a tiny bit different. There's a lot more airports, for "
                                "one, and there's a distinct lack of a screen, because it's Discord. I'm working on "
                                "that. For now though, use ``z!planes map`` to view all the airports, and "
                                "``z!planes help`` to view all the possible commands.\n\n"
                                "Important side note: One in-game hour is equal to one real-life minute. "
                                "Everything else is to scale.")

    if func.lower() == "init":
        # only function defined outside of PlanesInterpreter class, because all others
        # depend on it having been run first
        if ctx.message.author.id != kaisid:
            return await errsay("You don't have permission to do that.")
        try:
            re = len(pn.cities) != 0
            message = await planesay("{}nitializing...".format("Re-i" if re else "I"))
            start = time()
            mp = pn.MapParser()
            mp.feed(pn.readurl(pn.url))
            m = pn.Map(mp.json)
        except IndexError or sk.HTTPError:
            return await errsay("Initialization failed.")
        else:
            for i in range(len(m.cities)):
                pn.City(m.cities[i], m.coords[i], m.descs[i], i)
            tempcoun, coundict = {}, {g.name: g.value["Country"] for g in list(pn.cities.values())}
            for i in coundict:  # I have literally no clue why it doesn't like this get() sometimes
                tempcoun[coundict[i]] = tempcoun.get(coundict[i], []) + [pn.cities[i.lower()]]
            for i in tempcoun:
                pn.Country(i, tempcoun[i])
            with open("storage/planes.txt", "r") as read:
                for i in read.readlines():
                    pn.us(i)
            print([g.name for g in pn.countries.values() if g.name not in planemojis])
            return await client.edit_message(message, embed=consucc(
                "Planes {}initialized. ({} s)".format("re-" if re else "", round(time() - start, 1))))

    return await PlanesInterpreter(ctx).interpret(func, *args)


async def planesay(s, **kwargs):
    return await emolsay(":airplane:", s, hexcol("3a99f7"), **kwargs)


def conplane(s, **kwargs):  # for editing
    return conembed(title=f":airplane: \u2223 {s}", color=hexcol("3a99f7"), **kwargs)


class PlanesInterpreter:
    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.au = ctx.message.author
        self.channel = ctx.message.channel

    @staticmethod
    def form_et(n):  # formats remaining time
        return round(n) if round(n) >= 1 else "<1"

    @staticmethod
    def form_dt(dt: datetime):  # used to create timer URLs
        return "".join("".join("T".join(str(dt).split()).split("-")).split(":")).split(".")[0]

    @staticmethod
    def fluctuate(x: float):
        return sin(3 * x / 13) + cos(3 * x / 7) - sin(3 * x / 17) * cos(3 * x / 11)

    @staticmethod
    def invalid_city(s: str):
        return f"invalid city {s.lower()}. Did you mean {pn.cities[best_guess(s.lower(), pn.cities)].name}?"

    @staticmethod
    def valid_job(s: str):
        try:
            pn.js(s)
        except ValueError:
            return False
        if pn.js(s) not in pn.code_city(s[:2]).jobs:
            return False
        return True

    def oc(self, ci: pn.City, flag=False):
        flag = (":flag_" + planemojis[ci.country] + ": ") if flag else ""
        return flag + (ci.name if ci.name in pn.users[self.au.id].cities else "_{}_".format(ci.name))

    def fuel_price(self):
        return round(0.2 * self.fluctuate(time() // 86400), 2) + 1

    def model_prices(self):
        def precio(model: pn.Model):
            return self.fluctuate(time() // 86400 + 750 * list(pn.craft.keys()).index(model.name.lower()))
        return {g.name.lower(): round(g.cost + 0.1 * g.cost * precio(g)) for g in pn.craft.values()}

    async def iterate(self, p: pn.Plane):  # moves plane along path
        def pay_str():
            return f" and delivered Ȼ{ret_pay} in jobs" if ret_pay != 0 else ""

        tm, ret_path, ret_pay = time(), [p.path.fro.name], 0
        if len(p.path) == 0:
            return
        while len(p.path) > 0:
            if p.travel(p.path[0], p.path[1]) + p.path.time <= tm:
                ret_path.append(p.path[1].name)
                for job in copy(p.jobs):
                    if pn.js(job).destination == p.path[1]:
                        ret_pay += pn.js(job).pay
                        p.unload(job)
                p.path.iterate(p.travel(p.path[0], p.path[1]))
            else:
                if len(ret_path) == 1:
                    return
                pn.users[self.au.id].credits += ret_pay
                rewriteplanes()
                return await planesay(f"{p.name} passed through {len(ret_path) - 1} airport(s){pay_str()}!",
                                      d=f"arrives at {p.path[-1].name} in {pn.hrmin(p.arrival() - tm)}",
                                      footer="→".join(ret_path))
        pn.users[self.au.id].credits += ret_pay
        rewriteplanes()
        return await planesay(f"{p.name} arrived at {p.path[-1].name}{pay_str()}!", footer="→".join(ret_path))

    def filter_jobs(self, city: pn.City, fil: callable):
        tm = time()
        if tm - city.job_reset >= 900:
            print(f"generating jobs for {city.name}")
            city.rpj()
        gen = [g for g in city.jobs if g.code not in pn.users[self.au.id].jobs() and fil(g)]
        gen = [f"**``[{g.code}]``**  {self.oc(g.destination, True)}  (Ȼ{g.pay})" for g in gen]
        reset = tm // 900 * 900
        if tm - city.job_reset >= 900:
            city.job_reset = reset
        return {
            "table": gen,
            "footer": f"new jobs in {self.form_et(((tm // 900 + 1) * 900 - tm) // 60)} min"
        }

    async def f_navigate(self, message: discord.Message, d: dict, per: int, s: str, footer: str=None, il: bool=False):
        page = 1
        l = list(d.keys())
        pgs = ceil(len(l) / per)
        await client.add_reaction(message, "◀")
        await client.add_reaction(message, "▶")
        while True:
            command = await client.wait_for_reaction(message=message, timeout=300,
                                                     check=lambda c, u: c.emoji in ["◀", "▶"]
                                                     and u.id == self.au.id)
            if command is None:
                return
            page = (page + (-1 if command.reaction.emoji == "◀" else 1) - 1) % pgs + 1
            await client.edit_message(message, embed=conplane(s.format(page=page),
                                                              fs={g: d[g] for g in page_list(l, per, page)},
                                                              il=il, footer=footer))
            try:
                await client.remove_reaction(message, command.reaction.emoji, self.au)
            except discord.errors.Forbidden:
                pass

    '''INTERPRET METHOD. runs functions given from planes()'''

    async def interpret(self, func: str, *args: str):
        if len(pn.cities) == 0:
            return await errsay("Planes has not been initialized.")

        if self.au.id not in pn.users:
            await planesay("You haven't started Planes yet. What city would you like to start in?",
                           d="Use ``z!planes map`` to see a map of all cities. You can choose any one!",
                           footer="Just say the city name to pick - make sure to omit spaces.")
            while True:
                cho = await client.wait_for_message(timeout=300, author=self.au, channel=self.channel,
                                                    check=lambda c: len(c.content.split()) == 1)
                if cho is None:
                    return await planesay(f"{self.au.display_name}'s request timed out.")
                if cho.content.lower() in pn.cities:
                    cho = cho.content.lower()
                    cit = pn.cities[cho]
                    nam = choice(pn.starter_names)
                    pn.User(self.au.id, [cit.value["Country"]], [cit.name],
                            {nam.lower(): pn.Plane(pn.craft["tyne-647"], nam, pn.Path(0, cit), [], [0, 0])}, 1000000)
                    rewriteplanes()
                    await planesay(f"Great! {pn.cities[cho].name} Airport purchased.",
                                   footer="Anyway, that command...")
                    await asyncio.sleep(1)
                    break
                await planesay("That's not a recognized city.")

        for i in pn.users[self.au.id].planes.values():
            await self.iterate(i)

        redirects = {"city": "airport", "offload": "unload"}

        functions = dict([g for g in inspect.getmembers(PlanesInterpreter, predicate=inspect.isroutine)
                          if g[0][0] == "_" and g[0][1] != "_"])
        try:
            return await functions["_" + redirects.get(func.lower(), func.lower())](self, *args)
        except KeyError:
            return await errsay(f"unrecognized function {func}")

    '''ACTUAL FUNCTIONS OF THE GAME'''

    async def _help(self, *args):
        help_dict = {"map": "``z!planes map`` links to the airport map.",
                     "profile": "``z!planes profile`` shows your country licenses and credit balance.",
                     "fleet": "``z!planes fleet`` lists your owned planes.\n"
                              "``z!planes fleet <plane>`` shows specs for a specific plane.\n"
                              "``z!planes fleet sell <plane>`` sells a plane for 25% of its purchase value, including "
                              "money spent on upgrades.",
                     "country": "``z!planes country <country>`` shows information for a country.\n"
                                "``z!planes country buy <country>`` buys the license to a country.",
                     "airport": "``z!planes airport <airport>`` shows information for am airport.\n"
                                "``z!planes airport buy <airport>`` buys the airport.\n"
                                "``z!planes airport sell <airport>`` sells the airport for 25% of its purchase value.",
                     "model": "``z!planes model <model>`` shows specs for a plane model.",
                     "dist": "``z!planes dist <from> <to>`` returns the distance between two airports.\n"
                             "``z!planes dist <airports>`` returns the length of a path along multiple airports.",
                     "jobs": "``z!planes jobs <airport> [page]`` lists available jobs in an airport.\n"
                             "``z!planes jobs <airport> all [page]`` lists all jobs headed to all airports, "
                             "including those you don't own.",
                     "launch": "``z!planes launch <plane> <airports>`` launches a plane along a path. Be sure to "
                               "keep fuel prices in mind. The ETA in the launch message links to a countdown timer "
                               "to arrival.\n\nYou can chain airports using the ``launch`` command. For example:\n"
                               "``z!planes launch meadowlark washington newyork boston`` will tell Meadowlark to "
                               "follow the path from its current location to Washington, then NewYork, then Boston, "
                               "without stopping. Planes will automatically unload jobs along the way.",
                     "fuel": "``z!planes fuel`` shows the day's fuel prices. Prices change at midnight UTC.",
                     "load": "``z!planes load <plane> <job codes>`` loads jobs onto a plane. The job code is the "
                             "five-letter/number code on the left side of a job list.",
                     "unload": "``z!planes unload <plane> <job codes>`` unloads jobs from a plane without pay, "
                               "returning it to its original source.",
                     "rename": "``z!planes rename <plane> <new name>`` renames plane. Names can only contain "
                               "alphanumeric characters, dashes, and underscores.",
                     "market": "``z!planes market [page]`` shows prices for all available plane models. Like fuel, "
                               "plane prices fluctuate daily.\n"
                               "``z!planes market buy <model>`` purchases a new craft.",
                     "eta": "``z!planes eta <plane>`` links to the timer for a plane's arrival.",
                     "cities": "``z!planes cities <country> [page]`` lists all airports in a certain country, ordered "
                               "by traffic.",
                     "unowned": "``z!planes unowned <country> [page]`` lists unowned airports in a certain country, "
                                "ordered by traffic.",
                     "stats": "``z!planes stats <plane>`` shows the airspeed, fuel consumption, fuel capacity, and "
                              "upgrade levels for a plane you own.",
                     "upgrade": "``z!planes upgrade <plane> <stat>`` allows you to upgrade a plane. Each upgrade costs "
                                "Ȼ20,000 plus an additional Ȼ20,000 per already installed upgrade. A plane can go up "
                                "to level 3 in each stat.\n"
                                "``z!planes upgrade <plane> power`` increases a plane's airspeed by 25%, but also "
                                "increases its fuel consumption by 25%, so its range is not affected.\n"
                                "``z!planes upgrade <plane> tank`` increases a plane's fuel capacity by 25%, which "
                                "increases its range but does not affect its airspeed or fuel consumption."}
        if len(args) == 0 or args[0].lower() not in help_dict:
            return await planesay("z!planes help",
                                  d=f"Available functions:\n```{', '.join(list(help_dict.keys()))}```"
                                    f"For information on how to use these, use ``z!planes help <function>``.")
        return await planesay(f"z!planes {args[0].lower()}", d=help_dict[args[0].lower()])

    async def _map(self, *args):  # needs to be able to take args like all other commands
        return await planesay("Purchasable airports:", d=pn.url)

    async def _profile(self, *args):  # also needs to be able to take args
        return await planesay("{}'s Profile".format(self.au.display_name),
                              fs={"Licenses": " ".join([f":flag_{planemojis[g]}:"
                                                        for g in pn.users[self.au.id].countries]),
                                  "Credits": "Ȼ{}".format(pn.addcomm(round(pn.users[self.au.id].credits)))})

    async def _fleet(self, *args):
        if len(args) == 0:
            return await planesay("{}'s Fleet".format(self.au.display_name),
                                  fs={p.name: p.fleet_str() for p in pn.users[self.au.id].planes.values()}, il=True)
        if args[0] == "sell":
            if len(args) == 1:
                return await errsay("no plane input")
            args = args[1], args[0]
        if args[0].lower() not in pn.users[self.au.id].planes:
            return await planesay("no owned plane by that name")
        plane = pn.users[self.au.id].planes[args[0].lower()]
        if len(args) > 1 and args[1] == "sell":
            resale = int(self.model_prices()[plane.model.lower()] / 4)
            if await confirm(self.au, f"You're selling {plane.name} for Ȼ{pn.addcomm(resale)}."):
                pn.users[self.au.id].planes = \
                    {i: g for i, g in pn.users[self.au.id].planes.items() if g.name != plane.name}
                pn.users[self.au.id].credits += resale
                rewriteplanes()
                return await succsay("Plane sold.")
            return await planesay("Sale cancelled.")
        return await planesay(plane.name, fs=plane.dict(), il=True)

    async def _stats(self, *args):
        if len(args) == 0:
            return await errsay("no plane input")
        if args[0].lower() not in pn.users[self.au.id].planes:
            return await errsay("no owned plane by that name")
        plane = pn.users[self.au.id].planes[args[0].lower()]
        return await planesay(plane.name, fs=plane.stats(), il=True)

    async def _country(self, *args):
        if len(args) == 0:
            return await errsay("Please input a country.")
        if args[0].lower() == "buy":
            if len(args) == 1:
                return await errsay("no country input")
            args = args[1], args[0], *args[2:]
        try:
            country = pn.find_country(args[0])
        except KeyError:
            return await errsay("invalid country")
        if len(args) > 1 and args[1].lower() == "buy":
            if country.name in pn.users[self.au.id].countries:
                return await errsay("country already owned")
            price = round(country.worth)
            if price > pn.users[self.au.id].credits:
                return await errsay("not enough credits")
            if await confirm(self.au, f"You're buying the {country.name} license for Ȼ{pn.addcomm(price)}."):
                pn.users[self.au.id].credits -= price
                pn.users[self.au.id].countries.append(country.name)
                rewriteplanes()
                return await succsay("License purchased!")
            return await planesay("Purchase cancelled.")
        owned = len([g for g in pn.cities.values() if g.value["Country"] == country.name
                     and g.name in pn.users[self.au.id].cities])
        return await planesay(country.name,
                              fs={"Traffic": pn.suff(sum([g.passengers for g in country.cities])),
                                  "Cities": f"{len(country.cities)} ({owned} owned)",
                                  "License Value": "Ȼ{}".format(pn.addcomm(country.worth)),
                                  "Owned": yesDict[country.name in pn.users[self.au.id].countries],
                                  "Flag": f":flag_{planemojis[country.name]}:"}, il=True)

    async def _airport(self, *args):
        if len(args) == 0:
            return await errsay("Please input a function or airport.")
        if args[0].lower() in ["buy", "sell"]:
            if len(args) == 1:
                return await errsay("no airport input")
            args = args[1], args[0], *args[2:]
        try:
            city = pn.find_city(args[0])
        except KeyError:
            return await errsay(self.invalid_city(args[0]))
        if len(args) > 1 and args[1].lower() == "buy":
            if city.value["Country"] not in pn.users[self.au.id].countries:
                return await errsay("You don't have the {} license.".format(city.country))
            if city.name in pn.users[self.au.id].cities:
                return await errsay("airport already owned")
            price = round(city.worth)
            if price > pn.users[self.au.id].credits:
                return await errsay("not enough credits")
            if await confirm(self.au, f"You're buying {city.name} Airport for Ȼ{pn.addcomm(price)}."):
                pn.users[self.au.id].credits -= price
                pn.users[self.au.id].cities.append(city.name)
                rewriteplanes()
                return await succsay("Airport purchased!")
            else:
                return await planesay("Purchase cancelled.")
        if len(args) > 1 and args[1].lower() == "sell":
            if city.name not in pn.users[self.au.id].cities:
                return await errsay("airport not owned")
            resale = int(city.worth / 4)
            if await confirm(self.au, f"You're selling {city.name} Airport for Ȼ{pn.addcomm(resale)}."):
                pn.users[self.au.id].credits += resale
                pn.users[self.au.id].cities.remove(city.name)
                rewriteplanes()
                return await succsay("Airport sold!")
            return await planesay("Sale cancelled.")
        return await planesay(city.name + " Airport",
                              fs={**city.value, "Owned":
                                  {1: "Yes", 0: "No"}[city.name in pn.users[self.au.id].cities]}, il=True)

    async def _launch(self, *args):
        if len(args) == 0:
            return await errsay("What plane?")
        if len(args) == 1:
            return await errsay("To where?")
        if args[0].lower() not in pn.users[self.au.id].planes:
            return await errsay("That's not a plane you own.")
        plane, args = pn.users[self.au.id].planes[args[0].lower()], args[1:]
        if len(plane.path) != 0:
            return await errsay("That plane is currently in the air.")
        for arg in args:
            try:
                city = pn.find_city(arg)
            except KeyError:
                return await errsay(self.invalid_city(arg))
            if city.name not in pn.users[self.au.id].cities:
                return await errsay("You don't have the license to {}.".format(city.name))
        args = [pn.find_city(g) for g in args]
        path = [plane.path[0], *args]
        fuel_cost = 0
        for i in range(len(path) - 1):
            if path[i].dist(path[i + 1]) > plane.range:
                return await errsay(f"{plane.name} can't reach {path[i + 1].name} from {path[i].name}.")
            fuel_cost += round(plane.lpk * path[i].dist(path[i + 1]) * self.fuel_price(), 2)
        if round(fuel_cost) > pn.users[self.au.id].credits:
            return await planesay("You don't have enough money for fuel.")
        pn.users[self.au.id].credits -= round(fuel_cost)
        plane.launch(*args)
        rewriteplanes()
        url = pn.cd_url.format(self.form_dt(datetime.fromtimestamp(plane.arrival())),
                               f"{plane.name}+to+{plane.path[-1].name}")
        return await planesay("ETA: {}".format(pn.hrmin(plane.arrival() - time())), d=f"Fuel cost: Ȼ{round(fuel_cost)}",
                              url=url)

    async def _model(self, *args):
        if len(args) == 0:
            return await errsay("What model?")
        if args[0].lower() not in pn.craft:
            return await errsay("That's not a valid model.")
        plane = pn.blank_plane(args[0].lower())
        return await planesay(plane.model, d=f"*{pn.craft[plane.model.lower()].desc}*",
                              fs={"Airspeed": f"{plane.airspeed} km/hr", "Job Capacity": plane.passcap,
                                  "Fuel Usage": f"{plane.fueluse} L/hr ({plane.lpk} L/km)",
                                  "Fuel Tank": f"{plane.fuelcap} L", "Range": f"{plane.range} km",
                                  "Manufacturer": pn.craft[plane.model.lower()].maker}, il=True)

    async def _dist(self, *args):
        if len(args) == 0:
            return await planesay("no city input")
        if len(args) == 1:
            return await planesay("no destination input")
        try:
            pn.find_city(args[0])
        except KeyError:
            return await errsay(self.invalid_city(args[0]))
        st = 0
        for i in range(1, len(args)):
            try:
                pn.find_city(args[i])
            except KeyError:
                return await errsay(self.invalid_city(args[i]))
            st += pn.find_city(args[i - 1]).dist(pn.find_city(args[i]))
        return await planesay(f"{round(st, 2)} km")

    async def _priority(self, *args):
        if len(args) == 0:
            return await planesay("no city input")
        try:
            city = pn.find_city(args[0])
        except KeyError:
            return await errsay(self.invalid_city(args[0]))
        pri = sorted([g for g in pn.cities.values()], key=lambda x: -pn.priority(city, x))
        if len(args) != 1:
            try:
                to = pn.find_city(args[1])
            except KeyError:
                return await errsay(self.invalid_city(args[1]))
            name_pri = [g.name for g in pri]
            rank = name_pri.index(to.name) + 1
            return await planesay(f"{round(pn.priority(city, to), 2)} - "
                                  f"{[round(g, 2) for g in pn.priority(city, to, True)]}",
                                  d=f"Rank {rank}")
        return await planesay(f"Highest priority destinations from {city.name}",
                              d=", ".join([self.oc(j) for j in pri[:15]]))

    async def _jobs(self, *args):
        if len(args) == 0:
            return await planesay("no city input")
        try:
            city = pn.find_city(args[0])
        except KeyError:
            return await errsay(self.invalid_city(args[0]))
        tm = time()
        if tm - city.job_reset >= 900 or len(city.jobs) == 0:
            print(f"generating jobs for {city.name}")
            city.rpj()  # only rpj city when called
        fil = lambda j: j.destination.name in pn.users[self.au.id].cities
        fil_str = "J"
        if len(args) > 1 and args[1].lower() == "all":
            fil = lambda j: True
            fil_str = "All j"
        elif len(args) > 1 and args[1].lower().split(":")[0] == "to":
            if len(args[1].lower().split(":")) == 1:
                return await errsay("to where?")
            try:
                fil = lambda j: j.destination.country == pn.find_country(args[1].lower().split(":")[1]).name
                fil_str = f"{pn.find_country(args[1].lower().split(':')[1]).name} j"
            except KeyError:
                try:
                    fil = lambda j: j.destination.name == pn.find_city(args[1].lower().split(":")[1]).name
                    fil_str = f"{pn.find_city(args[1].lower().split(':')[1]).name} j"
                except KeyError:
                    return await errsay("invalid location")
        reset = tm // 900 * 900
        if tm - city.job_reset >= 900:
            city.job_reset = reset
        await JobNavigator(self, city, fil, fil_str,
                           footer=f"new jobs in {self.form_et(((tm // 900 + 1) * 900 - tm) // 60)} min").run(self.au)

    async def _rpj(self, *args):  # also needs to be able to take args
        if self.au.id != kaisid:
            return await errsay("insufficient permission")
        for i in pn.cities.values():
            i.jobs = []
            i.job_reset = 0
        return await succsay("Jobs regenerated.")

    async def _load(self, *args):
        if len(args) == 0:
            return await errsay("no airplane input")
        if args[0].lower() not in pn.users[self.au.id].planes:
            return await errsay("no owned plane by that name")
        if len(args) == 1:
            return await errsay("no job codes input")
        plane = pn.users[self.au.id].planes[args[0].lower()]
        if len(plane.path) != 0:
            return await errsay("plane is in the air")
        jobs = []
        for job in args[1:]:  # filters out duplicates while preserving input order
            if job not in jobs:
                jobs.append(job)
        for job in jobs:
            if not self.valid_job(job):
                return await errsay(f"invalid job code {job}")
            if job.upper() in pn.users[self.au.id].jobs():
                p = [g for g in pn.users[self.au.id].planes.values() if job.upper() in g.jobs][0]
                return await planesay(f"You've already loaded {job} onto {p.name}.")
            if pn.code_city(job[:2]) != plane.path[0]:
                return await errsay(f"plane is at different airport from {job}")
        for job in jobs:
            try:
                plane.load(job.upper())
            except ValueError:
                if jobs.index(job) == 0:
                    return await planesay("That plane is fully loaded.")
                else:
                    rewriteplanes()
                    return await succsay(f"Fully loaded plane with the first {jobs.index(job)} job(s).")
        rewriteplanes()
        return await succsay("Job loaded." if len(jobs) == 1 else "Jobs loaded.")

    async def _rename(self, *args):
        if len(args) == 0:
            return await errsay("no plane input")
        if args[0].lower() not in pn.users[self.au.id].planes:
            return await errsay("no owned plane by that name")
        nam = pn.users[self.au.id].planes[args[0].lower()].name
        if len(args) == 1:
            return await errsay("no name input")
        if [g in pn.permit for g in args[1]].count(False) != 0:
            return await errsay("plane names can only contain alphanumerics, dashes, and underscores")
        if args[1].lower() in pn.users[self.au.id].planes:
            return await errsay("a plane by that name already exists")
        if args[1].lower() == "sell":
            return await errsay("You can't name a plane that.")
        pn.users[self.au.id].rename(nam, args[1])
        rewriteplanes()
        return await succsay(f"{nam} renamed to {args[1]}.")

    async def _unload(self, *args):
        if len(args) == 0:
            return await errsay("no plane input")
        if args[0].lower() not in pn.users[self.au.id].planes:
            return await errsay("no owned plane by that name")
        plane = pn.users[self.au.id].planes[args[0].lower()]
        if len(plane.path) != 0:
            return await errsay("plane in air")
        if len(args) == 1:
            return await errsay("no job codes input")
        if args[1].lower() == "all":
            jobs = plane.jobs
        else:
            jobs = args[1:]
        for i in jobs:
            if i.upper() not in plane.jobs:
                return await errsay(f"invalid job code {i.upper()}")
        for i in jobs:
            plane.unload(i.upper())
        rewriteplanes()
        return await succsay(f"{plural('Job', len(jobs))} offloaded.")

    async def _fuel(self, *args):  # also needs to take args
        return await planesay(f"Today's fuel price: Ȼ{twodig(self.fuel_price())}/L")

    async def _market(self, *args):
        prices = self.model_prices()
        if len(args) > 0:
            if args[0].lower() != "buy":
                return await errsay(f"invalid function {args[0]}")
            if len(args) == 1:
                return await errsay("no purchase input")
            if args[1].lower() not in pn.craft:
                return await errsay("invalid model")
            model = args[1].lower()
            if prices[model] > pn.users[self.au.id].credits:
                return await planesay("You don't have enough credits.")
            if await confirm(self.au, f"You're buying a {pn.craft[model].name} for Ȼ{pn.addcomm(prices[model])}."):
                await succsay("Aircraft purchased! What would you like to name your new craft?")
                while True:
                    mess = await client.wait_for_message(timeout=300, author=self.au, channel=self.channel)
                    if mess is None:
                        return await planesay("Purchase timed out and cancelled.")
                    elif [g in pn.permit for g in mess.content].count(False) != 0:
                        await planesay("Plane names can only contain alphanumerics, dashes, and underscores.",
                                       d=f"What would you like to name your new {pn.craft[model].name}?")
                    elif mess.content.lower() in pn.users[self.au.id].planes:
                        await planesay("You already own a plane by that name.",
                                       d=f"What would you like to name your new {pn.craft[model].name}?")
                    elif mess.content.lower() == "sell":
                        await planesay("You can't name a plane that.",
                                       d=f"What would you like to name your new {pn.craft[model].name}?")
                    else:
                        await succsay(f"{pn.craft[model].name} named {mess.content}.")
                        new = pn.Plane(pn.craft[model], mess.content, pn.Path(0, pn.cities["london"]), [], [0, 0])
                        break
                await planesay(f"What city do you want to deploy {new.name} in?")
                while True:
                    mess = await client.wait_for_message(timeout=300, author=self.au, channel=self.channel,
                                                         check=lambda c: c.content.lower() in pn.cities)
                    if mess is None:
                        return await planesay("Purchase timed out and cancelled.")
                    elif pn.find_city(mess.content).name not in pn.users[self.au.id].cities:
                        await planesay(f"You don't own {pn.find_city(mess.content).name}.",
                                       d=f"What city do you want to deploy {new.name} in?")
                    else:
                        new.path = pn.Path(0, pn.find_city(mess.content))
                        pn.users[self.au.id].credits -= prices[model]
                        pn.users[self.au.id].planes[new.name.lower()] = new
                        rewriteplanes()
                        return await succsay(f"{new.name} ready for flight!")
        else:
            pgs = ceil(len(prices) / 6)
            prices = {pn.craft[g].name: f"Ȼ{pn.addcomm(prices[g])}" for g in prices}
            table = await planesay(f"The Market [1/{pgs}]",
                                   fs={g: prices[g] for g in list(prices.keys())[:6]}, il=True)
            return await self.f_navigate(table, prices, 6, "The Market [{page}/{pgs}]", il=True)

    async def _eta(self, *args):
        if len(args) == 0:
            return await errsay("no plane input")
        if args[0].lower() not in pn.users[self.au.id].planes:
            return await errsay("no owned plane by that name")
        plane = pn.users[self.au.id].planes[args[0].lower()]
        if len(plane.path) == 0:
            return await planesay(f"{plane.name} is landed.")
        url = pn.cd_url.format(self.form_dt(datetime.fromtimestamp(plane.arrival())),
                               f"{plane.name}+to+{plane.path[-1].name}")
        return await planesay(f"ETA: {pn.hrmin(plane.arrival() - time())}", url=url)

    async def _cities(self, *args):
        if len(args) == 0:
            return await errsay("no country input")
        try:
            country = pn.find_country(args[0]).name
        except KeyError:
            return await errsay("invalid country")
        ret = [g for g in pn.cities.values() if g.country == country]
        ret = [f"{g.name} ({g.value['Annual Passengers']})"
               for g in sorted(ret, key=lambda c: c.worth, reverse=True)]
        return await Navigator(conplane, ret, 6, "List of airports in " + country + " [{page}/{pgs}]").run(self.au)

    async def _unowned(self, *args):
        if len(args) == 0:
            return await errsay("no country input")
        try:
            country = pn.find_country(args[0]).name
        except KeyError:
            return await errsay("invalid country")
        ret = [g for g in pn.cities.values() if g.country == country
               and g.name not in pn.users[self.au.id].cities]
        cost = int(sum([g.worth for g in ret]))
        ret = [f"{g.name} (Ȼ{pn.addcomm(g.worth)})" for g in sorted(ret, key=lambda c: c.worth, reverse=True)]
        return await Navigator(conplane, ret, 6, "Unowned airports in " + country + " [{page}/{pgs}]",
                               footer=f"cost of all airports: Ȼ{pn.addcomm(cost)}").run(self.au)

    async def _upgrade(self, *args):
        if len(args) == 0:
            return await errsay("no plane input")
        if args[0].lower() not in pn.users[self.au.id].planes:
            return await errsay("no owned plane by that name")
        plane = pn.users[self.au.id].planes[args[0].lower()]
        if len(plane.path) != 0:
            return await errsay("That plane is currently in the air.")
        if len(args) == 1:
            return await errsay("no upgrade selected")
        ups = ["power", "tank"]
        if args[1].lower() not in ups:
            return await errsay("invalid upgrade")
        up_cost = round(20000 * sum(plane.upgrades + [1]))
        if up_cost > pn.users[self.au.id].credits:
            return await planesay(f"You don't have enough credits. Your next upgrade will cost Ȼ{pn.addcomm(up_cost)}.")
        if plane.upgrades[ups.index(args[1].lower())] == 3:
            return await planesay("You can't upgrade that further.")
        if await confirm(self.au, f"Are you sure you want to upgrade {plane.name}'s {args[1].lower()} for "
                                  f"Ȼ{pn.addcomm(up_cost)}?"):
            new_grade = [plane.upgrades[0] + (args[1].lower() == "power"),
                         plane.upgrades[1] + (args[1].lower() == "tank")]
            pn.users[self.au.id].credits -= up_cost
            pn.users[self.au.id].planes[plane.name.lower()] = \
                pn.Plane(pn.craft[plane.model.lower()], plane.name, plane.path, plane.jobs, new_grade)
            rewriteplanes()
            return await succsay("Plane upgraded!")
        return await planesay("Upgrade cancelled.")


class JobNavigator(Navigator):
    def __init__(self, inter: PlanesInterpreter, city: pn.City, fil: callable, fil_str: str, **kwargs):
        super().__init__(conplane, [], 8, fil_str + "obs in " + city.name + " [{page}/{pgs}]", **kwargs)
        self.interpreter = inter
        self.city = city
        self.fil = fil
        self.fil_str = fil_str
        self.update_jobs()
        self.funcs["🔄"] = self.update_jobs

    def update_jobs(self):
        self.page = 1
        ret = self.interpreter.filter_jobs(self.city, self.fil)
        self.table = ret["table"]
        self.pgs = ceil(len(self.table) / self.per)
        self.kwargs["footer"] = ret["footer"]
