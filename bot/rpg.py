from epitaph import *
from rpg_dir.map_refresher.refresher import Main as RPGRefresher

blockedTypes = ["mtn", "hrb", "hwl", "hsi", "idr", "bla", "fnt", "mtt", "sgn", "hrr", "hrp", "hrk"]
waterTypes = ["wtr"]


def limit(n: int, lower: int, upper: int):
    return lower if n < lower else upper if n > upper else n


async def rpgsay(s: str, **kwargs):
    return await client.say(embed=conrpg(s, **kwargs))


def conrpg(s: str, **kwargs):
    return conemol(getemoji("r_icon"), s, hexcol("10A840"), **kwargs)


def construct_warp(s: str):
    split = s.split("|")
    return split[0], (split[1] + ".txt", int(split[2]), int(split[3]), int(split[4]))


class Blocked(Exception):  # signifies player cannot move into a square
    pass


class Warp:  # both Warp and Sign are essentially just used as signifiers + redirects to a description
    def __init__(self, code: str):
        self.code = code


class Sign:
    def __init__(self, code: str):
        self.code = code


class Tile:
    def __init__(self, s: str):
        self.type = s[:3]
        self.display = getemoji("r_" + s[:5])
        self.fullType = s[:5]
        if len(s) == 5:
            self.data = None
        else:
            if s[5] == "W":
                self.data = Warp(s[6:])
            elif s[5] == "S":
                self.data = Sign(s[6:])
            else:
                self.data = None


class Map:
    def __init__(self, s: str):
        # inner lists are rows
        self.map = [[Tile(g) for g in reg_split(r"\s+", j)] for j in s.splitlines()]
        self.width = len(self.map[0])
        self.height = len(self.map)

    def print(self, x: int=0, y: int=0):
        return "\n".join(["".join([j.display for j in g[x:x+9]]) for g in self.map[y:y+7]])

    def table(self, x: int=0, y: int=0):
        return [[j.display for j in g[x:x+9]] for g in self.map[y:y+7]]


class BlankMap(Map):
    def __init__(self):
        with open("rpg_dir/blank.txt") as read:
            super().__init__(read.read())


class Player:
    def __init__(self):
        self.facing = 0
        self.frame = 0
        self.flippers = False

    def step(self, direction: int):
        if self.facing == direction:
            self.frame = (self.frame + 1) % 2
        else:
            self.frame = 0
        self.facing = direction

    def print(self):
        return getemoji("r_lnk" + "ludr"[self.facing] + str(self.frame))


class Game:
    def __init__(self, ctx: Context, player_pos: tuple=(42, 11)):
        # I would include these outside of __init__() but getemoji() can't be called until after the bot starts up
        self.buttons = ["◀", "🔼", "🔽", "▶", getemoji("r_bbutton", True), getemoji("r_abutton", True)]
        self.dir_coords = [[-1, 0], [0, -1], [0, 1], [1, 0]]
        self.mode_commands = {"map": ["⏹"]}

        self.message = null_message()
        self.au = ctx.message.author
        self.channel = ctx.message.channel
        with open("rpg_dir/maps/main.txt", "r") as read:
            self.map = BlankMap()
        self.mode = "map"
        self.player = Player()
        self.playerPos = list(player_pos)
        self.quit = False
        with open("rpg_dir/warps.txt") as read:
            self.warps = dict(construct_warp(g) for g in read.readlines())
        with open("rpg_dir/signs.txt") as read:
            self.signs = [g.split("|") for g in read.readlines()]
        self.signs = {g[0]: g[1].split("~") for g in self.signs}
        with open("rpg_dir/descs.txt") as read:
            self.descs = [g.split("|") for g in read.readlines()]
        self.descs = {g[0]: g[1].split("~") for g in self.descs}
        self.footer = None

    async def init(self):
        self.message = await rpgsay("Starting up...")
        for emoji in self.buttons + self.mode_commands[self.mode]:
            await client.add_reaction(self.message, emoji)
        await asyncio.sleep(0.5)
        await self.warp(Warp("000"), False)
        await self.update_screen()

    async def update_screen(self):
        await client.edit_message(self.message, embed=conrpg("ZRPG", d=self.print(), footer=self.footer))

    async def process(self, emoji: str):  # processes a button input
        if self.mode == "map":
            if emoji in self.buttons[:4]:
                self.player.step(self.buttons.index(emoji))
                try:
                    self.relative_move(self.dir_coords[self.buttons.index(emoji)])
                except Blocked:
                    pass
            if emoji == "⏹":
                self.quit = True
            if emoji == self.buttons[4]:
                self.footer = None
            if emoji == self.buttons[5]:
                self.check()
        await client.remove_reaction(self.message, emoji, self.au)

    def move(self, x: int, y: int):
        if limit(x, 0, self.map.width) != x or limit(y, 0, self.map.height) != y:
            raise Blocked
        if self.map.map[y][x].type in blockedTypes:
            raise Blocked
        if self.map.map[y][x].type in waterTypes and not self.player.flippers:
            raise Blocked
        self.playerPos = [x, y]

    def relative_move(self, coords: iter):
        self.move(self.playerPos[0] + coords[0], self.playerPos[1] + coords[1])

    def check(self, coords: iter=None):  # interacts with a tile
        if coords is None:
            coords = self.playerPos[0] + self.dir_coords[self.player.facing][0],\
                self.playerPos[1] + self.dir_coords[self.player.facing][1]
        tile = self.map.map[coords[1]][coords[0]]
        if type(tile.data) == Sign:
            self.read_sign(tile.data)
        else:
            try:
                self.describe_tile(tile)
            except KeyError:
                pass

    def print(self):
        if self.mode == "map":
            camera_x = limit(self.playerPos[0] - 4, 0, self.map.width - 9)
            camera_y = limit(self.playerPos[1] - 3, 0, self.map.height - 7)
            ret = self.map.table(camera_x, camera_y)
            ret[self.playerPos[1] - camera_y][self.playerPos[0] - camera_x] = self.player.print()
            return "\n".join(["".join(j) for j in ret])

    async def post_processing(self):
        if type(self.map.map[self.playerPos[1]][self.playerPos[0]].data) == Warp:
            await self.warp(self.map.map[self.playerPos[1]][self.playerPos[0]].data)

    async def warp(self, warp: Warp, aes: bool=True):
        if aes:
            await client.edit_message(self.message, embed=conrpg("ZRPG", d=BlankMap().print()))
        with open("rpg_dir/maps/" + self.warps[warp.code][0]) as read:
            self.map = Map(read.read())
        self.playerPos = self.warps[warp.code][1:3]
        self.player.facing = self.warps[warp.code][3]
        if aes:
            await asyncio.sleep(0.25)
            await self.update_screen()

    def advance_text(self, text: list):
        if self.footer in text:
            if text.index(self.footer) == len(text) - 1:
                self.footer = None
            else:
                self.footer = text[text.index(self.footer) + 1]
        else:
            self.footer = text[0]

    def read_sign(self, sign: Sign):
        self.advance_text(self.signs[sign.code])

    def describe_tile(self, tile: Tile):  # assumes object has description
        self.advance_text(self.descs[tile.fullType])

    async def run(self):
        await self.init()
        while True:
            command = await client.wait_for_reaction(message=self.message, timeout=300, user=self.au,
                                                     check=lambda c, u: c.emoji in
                                                     self.buttons + self.mode_commands[self.mode])
            if command is None:
                self.quit = True
                break
            await self.process(command.reaction.emoji)
            if self.quit:
                break
            await self.update_screen()
            await self.post_processing()
        await self.shut_down()

    async def shut_down(self):
        await client.edit_message(self.message, embed=conrpg("Shutting down..."))
        await client.clear_reactions(self.message)
        await asyncio.sleep(2)
        await client.delete_message(self.message)


class RPGDirNavigator(Navigator):
    def __init__(self, path: str):
        self.path = path
        self.folders = 0
        self.per = 6
        super().__init__(conrpg, self.format_dirs(), 6, "/".join(path.split("/")[1:]) + " [{page}/{pgs}]")
        self.funcs["⬆"] = self.up
        self.funcs[getemoji("folder1", True)] = self.one
        self.funcs[getemoji("folder2", True)] = self.two
        self.funcs[getemoji("folder3", True)] = self.three
        self.funcs[getemoji("folder4", True)] = self.four
        self.funcs[getemoji("folder5", True)] = self.five
        self.funcs[getemoji("folder6", True)] = self.six

    def format_dirs(self):
        ret = sorted(os.listdir(self.path), key=lambda c: ("1_" if c.endswith(".txt") else "0_") + c)
        self.folders = len([g for g in ret if not g.endswith(".txt")])
        return [f":page_facing_up: {g}" if g.endswith(".txt") else
                f"{getemoji('folder' + str(ret.index(g) % self.per + 1))} {g}" for g in ret]

    def retitle(self):
        self.title = "/".join(self.path.split("/")[1:]) + " [{page}/{pgs}]"

    async def up(self):
        if self.path == "rpg_dir/maps":
            return
        self.path = "/".join(self.path.split("/")[:-1])
        self.retitle()
        self.table = self.format_dirs()
        self.page = 0

    async def down(self, n: int):
        try:
            self.path = self.path + "/" + " ".join(page_list(self.table, self.per, self.page)[n].split()[1:])
            self.retitle()
            self.table = self.format_dirs()
            self.page = 0
        except IndexError:
            pass
        except NotADirectoryError:
            pass

    async def one(self):
        await self.down(0)

    async def two(self):
        await self.down(1)

    async def three(self):
        await self.down(2)

    async def four(self):
        await self.down(3)

    async def five(self):
        await self.down(4)

    async def six(self):
        await self.down(5)


@client.command(pass_context=True)
async def rpg(ctx: Context, func: str=None, *args: str):
    if func is None:
        return await rpgsay("An RPG or whatever.",
                            d="I have big plans for this but I know I'll never finish it. For now just dick around "
                              "with ``z!rpg play``.\n\nNote that Discord limits how often a bot can edit a message, "
                              "so if you hit buttons too quickly, every so often it'll take a bit longer to process. "
                              "I can't get around this and I'm sorry.")

    if func.lower() == "help":
        return await rpgsay("Help",
                            d=f"``z!rpg play`` plays the game.\nWhen the \"screen\" pops up, Zephyrus will add several "
                              f"reactions to the message. These reactions can be used as buttons!\nThe ◀🔼🔽▶ "
                              f"buttons are used as directional inputs - walking around or navigating a menu.\nThe ⏹ "
                              f"button will save and quit the game.\nThe {getemoji('r_abutton')} button will interact "
                              f"with several objects on the map, talk to people, and select menu options.\nThe "
                              f"{getemoji('r_bbutton')} button will close or back out of menus.")

    if func.lower() == "play":
        game = Game(ctx)
        return await game.run()

    if ctx.message.author.id != kaisid:
        return await errsay("insufficient permissions")

    if func.lower() == "warp":
        with open("rpg_dir/warps.txt", "r") as read:
            existing_warps = dict(construct_warp(g) for g in read.readlines())
            try:
                existing_warps[args[0].lower()] = args[1] + ".txt", int(args[2]), int(args[3]), int(args[4])
            except ValueError:
                return await errsay("Format: z!rpg warp <name> <file> <x> <y> <dir>")
            except IndexError:
                try:
                    return await rpgsay(" | ".join([str(g) for g in existing_warps.get(args[0].lower(), ["none"])]),
                                        d="Format: ``z!rpg warp <name> <file> <x> <y> <dir>``")
                except IndexError:
                    return await errsay("no name input")
        with open("rpg_dir/warps.txt", "w") as read:
            read.write("\n".join([f"{g}|{j[0].split('.')[0]}|{j[1]}|{j[2]}|{j[3]}"
                                  for g, j in sorted(existing_warps.items(), key=lambda c: c[0])]))
        return await succsay("done")

    if func.lower() == "sign":
        with open("rpg_dir/signs.txt", "r") as read:
            existing_signs = {g.split("|")[0]: g.split("|")[1].split("~") for g in read.readlines()}
            if len(args) == 0:
                return await errsay("Format: z!rpg sign <name> <line 1> ~ <line 2> ~ <etc>")
            if len(args) == 1:
                try:
                    return await rpgsay(existing_signs[args[0].lower()][0],
                                        d="\n".join(existing_signs[args[0].lower()][1:]))
                except KeyError:
                    return await rpgsay("no sign by that name")
            existing_signs[args[0].lower()] = reg_split(r"\s*~\s*", " ".join(args[1:]))
        with open("rpg_dir/signs.txt", "w") as read:
            read.write("\n".join([f"{g}|{'~'.join(j)}" for g, j in
                                  sorted(existing_signs.items(), key=lambda c: c[0])]))
        return await succsay("done")

    refresher = RPGRefresher()

    if func.lower() == "save":
        message = await rpgsay("saving...")
        try:
            refresher.save(sheet=args[0], map_file="/".join(args[1:]))
        except ValueError as v:
            return await errsay(v)
        except IndexError:
            return await rpgsay("Format: z!rpg save <sheet> <path>")
        else:
            return await client.edit_message(message, embed=consucc("done"))

    if func.lower() == "open":
        func = "load"

    if func.lower() == "load":
        stages = ["creating sheet...", "uploading map...", "formatting sheet...", ""]
        joiner = " done\n"
        message = await rpgsay("Loading...", d="creating sheet...")
        try:
            refresher.create(sheet=args[-1], map_file="/".join(args[0:-1]))
            await client.edit_message(message, embed=conrpg("Loading...", d=joiner.join(stages[:2])))
            refresher.load(sheet=args[-1], map_file="/".join(args[0:-1]))
            await client.edit_message(message, embed=conrpg("Loading...", d=joiner.join(stages[:3])))
            refresher.format(args[-1])
            await client.edit_message(message, embed=conrpg("Loading...", d=joiner.join(stages[:4])))
            await asyncio.sleep(0.25)
        except ValueError as v:
            return await errsay(v)
        except IndexError:
            return await rpgsay("Format: z!rpg load <path> <sheet>")
        else:
            return await client.edit_message(message, embed=consucc("done"))

    if func.lower() == "new":
        stages = ["creating...", "formatting...", ""]
        joiner = " done\n"
        message = await rpgsay("Loading...", d=stages[0])
        sheet_name = args[0] if len(args) else "new"
        try:
            refresher.create(sheet=sheet_name)
            await client.edit_message(message, embed=conrpg("Loading...", d=joiner.join(stages[:2])))
            refresher.format(sheet=sheet_name)
            await client.edit_message(message, embed=conrpg("Loading...", d=joiner.join(stages[:3])))
            await asyncio.sleep(0.25)
        except ValueError as v:
            return await errsay(v)
        else:
            return await client.edit_message(message, embed=consucc("done"))

    if func.lower() == "dir":
        path = f"rpg_dir/maps/{'/'.join(args)}" if len(args) > 0 else "rpg_dir/maps"
        try:
            return await RPGDirNavigator(path).run(ctx.message.author)
        except FileNotFoundError:
            return await rpgsay("Directory not found.")

    if func.lower() == "create":
        func = "makedir"

    if func.lower() == "makedir":
        if len(args) == 0:
            return await errsay("No directory input.")
        path = f"rpg_dir/maps/{'/'.join(args)}"
        try:
            os.makedirs(path)
            return await succsay(f"Path {path} created.")
        except FileExistsError:
            return await rpgsay("Directory already exists.")

    if func.lower() == "delete":
        if len(args) == 0:
            return await errsay("No path input.")
        path = f"rpg_dir/maps/{'/'.join(args)}"
        try:
            os.remove(path)
            return await rpgsay("File deleted.")
        except OSError:
            try:
                conf = await confirm(ctx.message.author, f"Are you sure you want to delete the directory {path}? It "
                                                         f"contains {len(os.listdir(path))} files and directories.",
                                     say=rpgsay)
                if not conf:
                    return await rpgsay("Deletion cancelled.")
                os.rmdir(path)
                return await rpgsay("Directory deleted.")
            except FileNotFoundError:
                return await rpgsay("Path not found.")
