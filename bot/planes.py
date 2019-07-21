from epitaph import *
from minigames import planes as pn
from math import sin, cos
import datetime


async def initialize_planes():
    print("Initializing planes...")
    start = time.time()
    for i in re.findall(pn.pattern, pn.readurl(pn.url)):
        pn.City.from_html(i)
    if len(pn.cities) == 0:
        return print("Initialization failed.")
    for i in pn.cities.values():
        if i.country not in pn.countries:
            pn.Country.from_name_only(i.country)
    with open("storage/planes.txt", "r") as read:
        for i in read.readlines():
            us = pn.User.from_str(i)
            zeph.planeUsers[us.id] = us
    return print(f"Planes initialized. ({round(time.time() - start, 1)} s)")


@zeph.command(aliases=["p"])
async def planes(ctx: commands.Context, func: str = None, *args: str):
    """
    def lamb(n: Flint):
        return log(tan(pi / 4 + pi * n / 4))

    image = rk.Image.open("C:/Users/Kaesekaiser/Pictures/nqr/airport_map.png")
    assert isinstance(image, rk.Image.Image)
    image = image.convert("RGBA")

    for i in re.findall(pn.pattern, pn.readurl(pn.url)):
        city = pn.City.from_html(i)
        point = rk.Image.open("C:/Users/Kaesekaiser/Pictures/nqr/airport.png")
        for j in range(3):
            try:
                rk.merge_down(
                    point, image, int(round(city.coords[1] * 7996 / 360 + 7996 * j)),
                    -int(round((3671 - 3447) / lamb(1 / 9) * lamb(city.coords[0] / 90))) + 3671, True
                )
            except ValueError:
                pass
        print(city.name, city.coords)
    """

    if not func:
        print(len(pn.cities), len(pn.countries))
        return await plane.send(
            ctx, "Planes",
            d="I don't particularly know what this is. If you've ever played Pocket Planes on mobile, it's essentially "
              "that, but a tiny bit different. There's a lot more airports, for one, and there's a distinct lack of a "
              "screen, because it's Discord. I'm working on that. For now though, use ``z!planes map`` to view all "
              "the airports, and ``z!planes help`` to view all the possible commands.\n\n"
              "Important side note: One in-game hour is equal to one real-life minute. Everything else is to scale."
        )

    return await PlanesInterpreter(ctx).run(str(func).lower(), *args)


class PlanesInterpreter(Interpreter):
    redirects = {"offload": "unload", "city": "airport", "airports": "cities"}

    @property
    def user(self):
        try:
            assert isinstance(zeph.planeUsers[self.au.id], pn.User)
            return zeph.planeUsers[self.au.id]
        except KeyError:
            return pn.User(0, [], [], {}, 0)

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
        return f"invalid city {s.lower()}. Did you mean {pn.cities[best_guess(s.lower(), pn.cities)].name}?"

    @staticmethod
    def valid_job(s: str):
        try:
            pn.Job.from_str(s)
        except ValueError:
            return False
        if pn.Job.from_str(s) not in pn.code_city(s[:2]).jobs:
            return False
        return True

    def oc(self, ci: pn.City, flag=False):
        flag = (":flag_" + pn.planemojis[ci.country] + ": ") if flag else ""
        return flag + (ci.name if ci.name in self.user.cities else "_{}_".format(ci.name))

    @property
    def fuel_price(self):
        return round(0.2 * self.fluctuate(time.time() // 86400), 2) + 1

    @property
    def model_prices(self):
        def pre(model: pn.Model):
            return self.fluctuate(time.time() // 86400 + 750 * list(pn.craft.keys()).index(model.name.lower()))

        return {g.name.lower(): round(g.cost + 0.1 * g.cost * pre(g)) for g in pn.craft.values()}

    def plane_value(self, craft: pn.Plane):
        return self.model_prices[craft.model.lower()] + int(10000 * (2 ** sum(craft.upgrades + [1]) - 1))

    def next_stop(self, craft: pn.Plane):
        craft.path.iterate(craft.travel(craft.path[0], craft.path[1]))
        ret = 0
        jobs = [g for g in craft.jobs]
        for i in jobs:
            job = pn.Job.from_str(i)
            if job.destination == craft.path[0]:
                craft.unload(i)
                self.user.credits += job.pay
                ret += job.pay
        return ret

    async def arrival_timer(self, craft: pn.Plane):
        delivered = 0
        while len(craft.path) > 0:
            await asyncio.sleep(craft.travel(craft.path[0], craft.path[1]))
            delivered += self.next_stop(craft)

        job_str = f" and delivered Ȼ{pn.addcomm(delivered)} in jobs" if delivered else ""
        return await plane.send(
            self.ctx, f"{craft.name} arrived at {craft.path[-1].name}{job_str}!", d=self.au.mention
        )

    def filter_jobs(self, city: pn.City, fil: callable):
        tm = time.time()
        if tm - city.job_reset >= 900:
            print(f"generating jobs for {city.name}")
            city.rpj()
        gen = [g for g in city.jobs if g.code not in self.user.jobs and fil(g)]
        gen = [f"**``[{g.code}]``**  {self.oc(g.destination, True)}  (Ȼ{g.pay})" for g in gen]
        reset = tm // 900 * 900
        if tm - city.job_reset >= 900:
            city.job_reset = reset
        return {
            "table": gen,
            "footer": f"new jobs in {self.form_et(((tm // 900 + 1) * 900 - tm) // 60)} min"
        }

    async def before_run(self):
        if self.au.id not in zeph.planeUsers:
            if await confirm("You haven't started a Planes company yet. Would you like to?", self.ctx, self.au,
                             yes="start now", no="start later", emol=plane):
                def pred(m: discord.Message):
                    return m.author == self.au and m.channel == self.ctx.channel and len(m.content.split()) == 1

                await plane.send(
                    self.ctx, "Pick any city to start.", url=pn.url,
                    d="You'll get the license to that country along with it. Make sure to omit spaces."
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
                            zeph.planeUsers[self.au.id] = pn.User(
                                self.au.id, [cit.country], [cit.name],
                                {nam.lower(): pn.Plane(pn.craft["tyne-647"], nam, pn.Path(0, cit), [], [0, 0])}, 1000000
                            )
                            await plane.send(self.ctx, f"Great! {pn.cities[cho].name} Airport purchased.",
                                             footer="Anyway, that command...")
                            await asyncio.sleep(1)
                            break
                        await plane.send(self.ctx, "That's not a recognized city.")

        if self.au.id in zeph.planeUsers:
            for craft in self.user.planes.values():  # kinda messy; should only be called if zeph went down
                if len(craft.path) > 0:              # while a plane was in the air
                    while craft.next_eta and craft.next_eta < time.time():
                        self.next_stop(craft)

    async def _help(self, *args):
        help_dict = {
            "map": "``z!planes map`` links to the airport map.",
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
            "jobs": "``z!planes jobs <airport>`` lists available jobs in an airport.\n"
                    "``z!planes jobs <airport> all`` lists all jobs headed to all airports, "
                    "including those you don't own.\n"
                    "``z!planes jobs <airport> to <city/country>`` lists all jobs headed to a certain city or country.",
            "launch": "``z!planes launch <plane> <airports>`` launches a plane along a path. Be sure to "
                      "keep fuel prices in mind. The ETA in the launch message links to a countdown timer "
                      "to arrival, and Zephyrus will notify you when it's arrived.\n\n"
                      "You can chain airports using the ``launch`` command. For example:\n"
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
            "market": "``z!planes market`` shows prices for all available plane models. Like fuel, "
                      "plane prices fluctuate daily.\n"
                      "``z!planes market buy <model>`` purchases a new craft.",
            "eta": "``z!planes eta <plane>`` links to the timer for a plane's arrival.",
            "cities": "``z!planes cities <country>`` lists all airports in a certain country, ordered "
                      "by traffic.",
            "unowned": "``z!planes unowned <country>`` lists unowned airports in a certain country, "
                       "ordered by traffic.",
            "stats": "``z!planes stats <plane>`` shows the airspeed, fuel consumption, fuel capacity, and "
                     "upgrade levels for a plane you own.",
            "upgrade": "``z!planes upgrade <plane> <stat>`` allows you to upgrade a plane. Each upgrade costs "
                       "Ȼ20,000 plus an additional Ȼ20,000 per already installed upgrade. A plane can go up "
                       "to level 3 in each stat.\n"
                       "``z!planes upgrade <plane> power`` increases a plane's airspeed by 25%, but also "
                       "increases its fuel consumption by 25%, so its range is not affected.\n"
                       "``z!planes upgrade <plane> tank`` increases a plane's fuel capacity by 25%, which "
                       "increases its range but does not affect its airspeed or fuel consumption.",
            "buyout": "``z!planes buyout <country>`` buys as many airports in a certain country as you can afford, "
                      "starting with the biggest airports. For your personal convenience, so that you can quickly "
                      "expand into a new market without having to manually buy a ton of airports.\n"
                      "``z!planes buyout <country> <number>`` does the same, but will only buy, at most, ``<number>`` "
                      "airports."
        }

        if len(args) == 0 or (args[0].lower() not in help_dict and args[0].lower() not in self.redirects):
            return await plane.send(
                self.ctx, "z!planes help",
                d=f"Available functions:\n```{', '.join(list(help_dict.keys()))}```\n"
                f"For information on how to use these, use ``z!planes help <function>``."
            )

        ret = self.redirects.get(args[0].lower(), args[0].lower())

        return await plane.send(self.ctx, f"z!planes {ret}", d=help_dict[ret])

    async def _map(self, *args):  # needs to be able to take args like all other commands
        return await plane.send(self.ctx, "Purchasable airports:", d=pn.url)

    async def _profile(self, *args):  # also needs to be able to take args
        val = sum([pn.find_city(g).value for g in self.user.cities] +
                  [self.plane_value(g) for g in self.user.planes.values()])
        return await plane.send(
            self.ctx, "{}'s Profile".format(self.au.display_name), same_line=True,
            fs={"Licenses": NewLine(" ".join([f":flag_{pn.planemojis[g]}:" for g in self.user.countries])),
                "Credits": f"Ȼ{pn.addcomm(self.user.credits)}",
                "Airports": len(self.user.cities),
                "Airline Value": f"Ȼ{pn.addcomm(val)}"}
        )

    async def _fleet(self, *args):
        if len(args) == 0:
            return await plane.send(
                self.ctx, "{}'s Fleet".format(self.au.display_name),
                fs={p.name: p.fleet_str for p in self.user.planes.values()}, same_line=True
            )

        if args[0] == "sell":
            if len(args) == 1:
                raise commands.CommandError("no plane input")
            args = args[1], args[0]
        if args[0].lower() not in self.user.planes:
            return await plane.send(self.ctx, "no owned plane by that name")

        craft = self.user.planes[args[0].lower()]

        if len(args) > 1 and args[1] == "sell":
            if len(self.user.planes) == 1:
                return await plane.send(self.ctx, "You can't sell your last plane.")

            resale = int(self.model_prices[craft.model.lower()] / 4)
            if await confirm(f"You're selling {craft.name} for Ȼ{pn.addcomm(resale)}.", self.ctx, self.au):
                self.user.planes = \
                    {i: g for i, g in self.user.planes.items() if g.name != craft.name}
                self.user.credits += resale
                return await succ.send(self.ctx, "Plane sold.")

            return await plane.send(self.ctx, "Sale cancelled.")

        return await plane.send(self.ctx, craft.name, fs=craft.dict, same_line=True)

    async def _stats(self, *args):
        if len(args) == 0:
            raise commands.CommandError("no plane input")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("no owned plane by that name")

        craft = self.user.planes[args[0].lower()]
        return await plane.send(self.ctx, craft.name, fs=craft.stats, same_line=True)

    async def _country(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Please input a country.")
        if args[0].lower() == "buy":
            if len(args) == 1:
                raise commands.CommandError("no country input")
            args = args[1], args[0], *args[2:]

        try:
            country = pn.find_country(args[0])
        except KeyError:
            raise commands.CommandError("invalid country")

        assert isinstance(country, pn.Country)
        if len(args) > 1 and args[1].lower() == "buy":
            if country.name in self.user.countries:
                raise commands.CommandError("country already owned")

            price = round(country.worth)
            if price > self.user.credits:
                raise commands.CommandError("not enough credits")

            if await confirm(f"You're buying the {country.name} license for Ȼ{pn.addcomm(price)}.", self.ctx, self.au):
                self.user.credits -= price
                self.user.countries.append(country.name)
                return await succ.send(self.ctx, "License purchased!")

            return await plane.send(self.ctx, "Purchase cancelled.")

        owned = len([g for g in pn.cities.values() if g.country == country.name
                     and g.name in self.user.cities])
        return await plane.send(
            self.ctx, country.name, same_line=True,
            fs={"Traffic": pn.suff(sum([g.passengers for g in country.cities])),
                "Cities": f"{len(country.cities)} ({owned} owned)",
                "License Value": f"Ȼ{pn.addcomm(country.worth)}",
                "Owned": ["No", "Yes"][country.name in self.user.countries],
                "Flag": f":flag_{pn.planemojis[country.name]}:"}
        )

    async def _airport(self, *args):
        if len(args) == 0:
            raise commands.CommandError("Please input a function or airport.")
        if args[0].lower() in ["buy", "sell"]:
            if len(args) == 1:
                raise commands.CommandError("no airport input")
            args = args[1], args[0], *args[2:]

        try:
            city = pn.find_city(args[0])
        except KeyError:
            raise commands.CommandError(self.invalid_city(args[0]))

        assert isinstance(city, pn.City)
        if len(args) > 1 and args[1].lower() == "buy":
            if city.country not in self.user.countries:
                raise commands.CommandError("You don't have the {} license.".format(city.country))
            if city.name in self.user.cities:
                raise commands.CommandError("airport already owned")
            price = round(city.value)
            if price > self.user.credits:
                raise commands.CommandError("not enough credits")

            if await confirm(f"You're buying {city.name} Airport for Ȼ{pn.addcomm(price)}.", self.ctx, self.au):
                self.user.credits -= price
                self.user.cities.append(city.name)
                return await succ.send(self.ctx, "Airport purchased!")
            else:
                return await plane.send(self.ctx, "Purchase cancelled.")

        if len(args) > 1 and args[1].lower() == "sell":
            if city.name not in self.user.cities:
                raise commands.CommandError("airport not owned")

            resale = int(city.value / 4)
            if await confirm(f"You're selling {city.name} Airport for Ȼ{pn.addcomm(resale)}.", self.ctx, self.au):
                self.user.credits += resale
                self.user.cities.remove(city.name)
                return await succ.send(self.ctx, "Airport sold!")

            return await plane.send(self.ctx, "Sale cancelled.")

        return await plane.send(
            self.ctx, city.name + " Airport",
            fs={**city.dict, "Owned": ["No", "Yes"][city.name in self.user.cities]}, same_line=True
        )

    async def _launch(self, *args):
        if len(args) == 0:
            raise commands.CommandError("What plane?")
        if len(args) == 1:
            raise commands.CommandError("To where?")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("That's not a plane you own.")

        craft, args = self.user.planes[args[0].lower()], args[1:]
        if len(craft.path) != 0:
            raise commands.CommandError("That plane is currently in the air.")
        for arg in args:
            try:
                city = pn.find_city(arg)
            except KeyError:
                raise commands.CommandError(self.invalid_city(arg))
            if city.name not in self.user.cities:
                raise commands.CommandError("You don't have the license to {}.".format(city.name))

        args = [pn.find_city(g) for g in args]
        path = [craft.path[0], *args]
        fuel_cost = 0

        for i in range(len(path) - 1):
            if path[i].dist(path[i + 1]) > craft.range:
                raise commands.CommandError(f"{craft.name} can't reach {path[i + 1].name} from {path[i].name}.")

            fuel_cost += round(craft.lpk * path[i].dist(path[i + 1]) * self.fuel_price, 2)

        if round(fuel_cost) > self.user.credits:
            return await plane.send(self.ctx, "You don't have enough money for fuel.")

        self.user.credits -= round(fuel_cost)
        craft.launch(*args)
        url = pn.cd_url.format(
            self.form_dt(datetime.datetime.fromtimestamp(craft.arrival)),
            f"{craft.name}+to+{craft.path[-1].name}"
        )
        zeph.loop.create_task(self.arrival_timer(craft))
        return await plane.send(
            self.ctx, "ETA: {}".format(pn.hrmin(craft.arrival - time.time())),
            d=f"Fuel cost: Ȼ{round(fuel_cost)}", url=url
        )

    async def _model(self, *args):
        if len(args) == 0:
            raise commands.CommandError("What model?")
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
            return await plane.send(self.ctx, "no city input")
        if len(args) == 1:
            return await plane.send(self.ctx, "no destination input")

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

    async def _priority(self, *args):
        if len(args) == 0:
            return await plane.send(self.ctx, "no city input")
        try:
            city = pn.find_city(args[0])
        except KeyError:
            raise commands.CommandError(self.invalid_city(args[0]))

        pri = sorted([g for g in pn.cities.values()], key=lambda x: -pn.priority(city, x))
        if len(args) != 1:
            try:
                to = pn.find_city(args[1])
            except KeyError:
                raise commands.CommandError(self.invalid_city(args[1]))

            name_pri = [g.name for g in pri]
            rank = name_pri.index(to.name) + 1
            return await plane.send(
                self.ctx, f"{round(pn.priority(city, to), 2)} - {[round(g, 2) for g in pn.priority(city, to, True)]}",
                d=f"Rank {rank}"
            )

        return await plane.send(
            self.ctx, f"Highest priority destinations from {city.name}",
            d=", ".join([self.oc(j) for j in pri[:15]])
        )

    async def _jobs(self, *args):
        if len(args) == 0:
            return await plane.send(self.ctx, "no city input")
        try:
            city = pn.find_city(args[0])
        except KeyError:
            raise commands.CommandError(self.invalid_city(args[0]))

        tm = time.time()
        if tm - city.job_reset >= 900 or len(city.jobs) == 0:
            print(f"generating jobs for {city.name}")
            city.rpj()  # only rpj city when called

        fil = lambda j: j.destination.name in self.user.cities
        fil_str = "J"
        if len(args) > 1 and args[1].lower() == "all":
            fil = lambda j: True
            fil_str = "All j"
        elif len(args) > 1 and args[1].lower() == "to":
            if len(args) == 2:
                raise commands.CommandError("to where?")

            try:
                fil = lambda j: j.destination.country == pn.find_country(args[2].lower()).name
                fil_str = f"{pn.find_country(args[2].lower()).name} j"
            except KeyError:
                try:
                    fil = lambda j: j.destination.name == pn.find_city(args[2].lower()).name
                    fil_str = f"{pn.find_city(args[2].lower()).name} j"
                except KeyError:
                    raise commands.CommandError("invalid location")

        reset = tm // 900 * 900
        if tm - city.job_reset >= 900:
            city.job_reset = reset

        await JobNavigator(
            self, city, fil, fil_str,
            footer=f"new jobs in {self.form_et(((tm // 900 + 1) * 900 - tm) // 60)} min"
        ).run(self.ctx)

    async def _load(self, *args):
        if len(args) == 0:
            raise commands.CommandError("no airplane input")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("no owned plane by that name")
        if len(args) == 1:
            raise commands.CommandError("no job codes input")

        craft = self.user.planes[args[0].lower()]
        if len(craft.path) != 0:
            raise commands.CommandError("plane is in the air")

        jobs = []
        for job in args[1:]:  # filters out duplicates while preserving input order
            if job not in jobs:
                jobs.append(job)

        for job in jobs:
            if not self.valid_job(job):
                raise commands.CommandError(f"invalid job code {job}")
            if job.upper() in self.user.jobs:
                p = [g for g in self.user.planes.values() if job.upper() in g.jobs][0]
                return await plane.send(self.ctx, f"You've already loaded {job} onto {p.name}.")
            if pn.code_city(job[:2]) != craft.path[0]:
                raise commands.CommandError(f"plane is at different airport from {job}")

        for job in jobs:
            try:
                craft.load(job.upper())
            except ValueError:
                if jobs.index(job) == 0:
                    return await plane.send(self.ctx, "That plane is fully loaded.")
                else:
                    return await succ.send(self.ctx, f"Fully loaded plane with the first {jobs.index(job)} job(s).")

        return await succ.send(self.ctx, "Job loaded." if len(jobs) == 1 else "Jobs loaded.")

    async def _rename(self, *args):
        if len(args) == 0:
            raise commands.CommandError("no plane input")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("no owned plane by that name")

        nam = self.user.planes[args[0].lower()].name
        if len(args) == 1:
            raise commands.CommandError("no name input")
        if [g in pn.permit for g in args[1]].count(False) != 0:
            raise commands.CommandError("plane names can only contain alphanumerics, dashes, and underscores")
        if args[1].lower() in self.user.planes:
            raise commands.CommandError("a plane by that name already exists")
        if args[1].lower() == "sell":
            raise commands.CommandError("You can't name a plane that.")

        self.user.rename(nam, args[1])
        return await succ.send(self.ctx, f"{nam} renamed to {args[1]}.")

    async def _unload(self, *args):
        if len(args) == 0:
            raise commands.CommandError("no plane input")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("no owned plane by that name")

        craft = self.user.planes[args[0].lower()]
        if len(craft.path) != 0:
            raise commands.CommandError("plane in air")
        if len(args) == 1:
            raise commands.CommandError("no job codes input")

        if args[1].lower() == "all":
            jobs = craft.jobs
        else:
            jobs = args[1:]
        for i in jobs:
            if i.upper() not in craft.jobs:
                raise commands.CommandError(f"invalid job code ``{i.upper()}``")

        for i in jobs:
            craft.unload(i.upper())
        return await succ.send(self.ctx, f"{plural('Job', len(jobs))} offloaded.")

    async def _fuel(self, *args):  # also needs to take args
        return await plane.send(self.ctx, f"Today's fuel price: Ȼ{two_digit(self.fuel_price)}/L")

    async def _market(self, *args):
        prices = self.model_prices

        if len(args) > 0:
            if args[0].lower() != "buy":
                raise commands.CommandError(f"invalid function ``{args[0]}``")
            if len(args) == 1:
                raise commands.CommandError("no purchase input")
            if args[1].lower() not in pn.craft:
                raise commands.CommandError("invalid model")

            model = args[1].lower()
            if prices[model] > zeph.planeUsers[self.au.id].credits:
                return await plane.send(self.ctx, "You don't have enough credits.")

            if await confirm(f"You're buying a {pn.craft[model].name} for Ȼ{pn.addcomm(prices[model])}.",
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
                        if [g in pn.permit for g in mess.content].count(False) != 0:
                            await plane.send(self.ctx,
                                             "Plane names can only contain alphanumerics, dashes, and underscores.",
                                             d=f"What would you like to name your new {pn.craft[model].name}?")
                        elif mess.content.lower() in zeph.planeUsers[self.au.id].planes:
                            await plane.send(self.ctx, "You already own a plane by that name.",
                                             d=f"What would you like to name your new {pn.craft[model].name}?")
                        elif mess.content.lower() == "sell":
                            await plane.send(self.ctx, "You can't name a plane that.",
                                             d=f"What would you like to name your new {pn.craft[model].name}?")
                        else:
                            await succ.send(self.ctx, f"{pn.craft[model].name} named {mess.content}.")
                            new = pn.Plane.new(model)
                            new.name = mess.content
                            break

                await plane.send(self.ctx, f"What city do you want to deploy {new.name} in?")
                while True:
                    try:
                        mess = await zeph.wait_for("message", timeout=300, check=pred2)
                    except asyncio.TimeoutError:
                        return await plane.send(self.ctx, "Purchase timed out and cancelled.")

                    else:
                        if pn.find_city(mess.content).name not in zeph.planeUsers[self.au.id].cities:
                            await plane.send(self.ctx, f"You don't own {pn.find_city(mess.content).name}.",
                                             d=f"What city do you want to deploy {new.name} in?")
                        else:
                            new.path = pn.Path(0, pn.find_city(mess.content))
                            self.user.credits -= prices[model]
                            self.user.planes[new.name.lower()] = new
                            return await succ.send(self.ctx, f"{new.name} ready for flight!")

            else:
                return await plane.send(self.ctx, "Purchase cancelled.")

        else:
            prices = {pn.craft[g].name: f"Ȼ{pn.addcomm(prices[g])}" for g in prices}
            return await FieldNavigator(plane, prices, 6, "The Market [{page}/{pgs}]", same_line=True).run(self.ctx)

    async def _eta(self, *args):
        if len(args) == 0:
            raise commands.CommandError("no plane input")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("no owned plane by that name")

        craft = self.user.planes[args[0].lower()]
        if len(craft.path) == 0:
            return await plane.send(self.ctx, f"{craft.name} is landed.")
        url = pn.cd_url.format(self.form_dt(datetime.datetime.fromtimestamp(craft.arrival)),
                               f"{craft.name}+to+{craft.path[-1].name}")
        return await plane.send(self.ctx, f"ETA: {pn.hrmin(craft.arrival - time.time())}", url=url)

    async def _cities(self, *args):
        if len(args) == 0:
            raise commands.CommandError("no country input")
        try:
            country = pn.find_country(args[0])
        except KeyError:
            raise commands.CommandError("invalid country")

        ret = [f"{g.name} ({g.dict['Annual Passengers']})" for g in country.cities]
        return await Navigator(plane, ret, 6, "List of airports in " + country.name + " [{page}/{pgs}]").run(self.ctx)

    async def _unowned(self, *args):
        if len(args) == 0:
            raise commands.CommandError("no country input")
        try:
            country = pn.find_country(args[0]).name
        except KeyError:
            raise commands.CommandError("invalid country")

        ret = [g for g in pn.cities.values() if g.country == country
               and g.name not in self.user.cities]
        cost = int(sum([g.value for g in ret]))
        ret = [f"{g.name} (Ȼ{pn.addcomm(g.value)})" for g in sorted(ret, key=lambda c: c.value, reverse=True)]

        return await Navigator(
            plane, ret, 6, "Unowned airports in " + country + " [{page}/{pgs}]",
            footer=f"cost of all airports: Ȼ{pn.addcomm(cost)}"
        ).run(self.ctx)

    async def _upgrade(self, *args):
        if len(args) == 0:
            raise commands.CommandError("no plane input")
        if args[0].lower() not in self.user.planes:
            raise commands.CommandError("no owned plane by that name")

        craft = self.user.planes[args[0].lower()]
        if len(craft.path) != 0:
            raise commands.CommandError("That plane is currently in the air.")
        if len(args) == 1:
            raise commands.CommandError("no upgrade selected")

        ups = ["power", "tank"]
        if args[1].lower() not in ups:
            raise commands.CommandError("invalid upgrade")

        up_cost = int(10000 * 2 ** sum(craft.upgrades + [1]))
        if up_cost > self.user.credits:
            return await plane.send(
                self.ctx, f"You don't have enough credits. Your next upgrade will cost Ȼ{pn.addcomm(up_cost)}."
            )

        if await confirm(f"Are you sure you want to upgrade {craft.name}'s {args[1].lower()} for "
                         f"Ȼ{pn.addcomm(up_cost)}?", self.ctx, self.au):
            new_grade = [craft.upgrades[0] + (args[1].lower() == "power"),
                         craft.upgrades[1] + (args[1].lower() == "tank")]
            self.user.credits -= up_cost
            craft.upgrades = new_grade
            return await succ.send(self.ctx, "Plane upgraded!")
        return await plane.send(self.ctx, "Upgrade cancelled.")

    async def _buyout(self, *args):
        if len(args) == 0:
            raise commands.CommandError("no country input")
        try:
            country = pn.find_country(args[0])
        except KeyError:
            raise commands.CommandError(f"invalid country ``{args[0]}``")

        assert isinstance(country, pn.Country)
        if country.name not in self.user.countries:
            return await plane.send(self.ctx, f"You don't have the license to {country.name}.")

        if len(args) > 1:
            try:
                stop_at = int(args[1])
            except ValueError:
                stop_at = len(country.cities)
        else:
            stop_at = len(country.cities)

        bought, price, total = [], 0, True
        for city in country.cities:
            if sum([g.value for g in bought] + [city.value]) > self.user.credits or len(bought) == stop_at:
                if not bought:
                    return await plane.send(self.ctx, f"You can't afford the biggest airport in {country.name}.")
                total = False
                break

            if city.name not in self.user.cities:
                bought.append(city)
                price += city.value

        if not bought:
            return await plane.send(self.ctx, f"You already own every airport in {country.name}.")

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
                "``WARNING:`` This will completely and absolutely wipe your Planes data.", self.ctx, self.au,
                add_info="All progress will be lost, and you won't be able to get it back, except through your own "
                         "blood, sweat, and tears. Are you sure you want to start over?\n", yes="wipe everything"
            )
        except AssertionError:
            return await plane.send(self.ctx, "Game data not wiped.")
        else:
            mess = await plane.send(self.ctx, "Alright, one moment...")
            await asyncio.sleep(2 + random() * 2)
            del zeph.planeUsers[self.au.id]
            return await succ.edit(mess, "Done.", d="Call any ``z!planes`` function to start anew.")


class JobNavigator(Navigator):
    def __init__(self, inter: PlanesInterpreter, city: pn.City, fil: callable, fil_str: str, **kwargs):
        super().__init__(plane, [], 8, fil_str + "obs in " + city.name + " [{page}/{pgs}]", **kwargs)
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
        self.kwargs["footer"] = ret["footer"]
