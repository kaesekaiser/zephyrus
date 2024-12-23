import discord
from discord.ext import commands
from functions import hex_to_color


class NewLine:
    def __init__(self, obj):
        self.object = obj

    def __str__(self):
        return str(self.object)

    def __bool__(self):
        return bool(self.object)


class EmbedAuthor:
    def __init__(self, name, url=None, icon=None):
        self.name = name
        self.url = url
        self.icon = icon


def author_from_user(user: discord.User | discord.Member, name: str = None, url: str = None):
    return EmbedAuthor(name if name else f"{user.name}#{user.discriminator}", icon=user.avatar.url, url=url)


# SAME_LINE: IF TRUE, PUTS IN SAME LINE. IF FALSE, PUTS ON NEW LINE.
def construct_embed(**kwargs):
    title = kwargs.get("s", kwargs.get("title"))
    desc = kwargs.get("d", kwargs.get("desc"))
    color = kwargs.get("col", kwargs.get("color"))
    fields = kwargs.get("fs", kwargs.get("fields", {}))
    ret = discord.Embed(title=title, description=desc, colour=color)
    for i in fields:
        if len(str(fields[i])) != 0:
            ret.add_field(name=i, value=str(fields[i]),
                          inline=(False if isinstance(fields[i], NewLine) else kwargs.get("same_line", False)))
    if kwargs.get("footer"):
        ret.set_footer(text=kwargs.get("footer"))
    if kwargs.get("thumb", kwargs.get("thumbnail")):
        ret.set_thumbnail(url=kwargs.get("thumb", kwargs.get("thumbnail")))
    if kwargs.get("author"):
        ret.set_author(name=kwargs.get("author").name, url=kwargs.get("author").url, icon_url=kwargs.get("author").icon)
    if kwargs.get("url"):
        ret.url = kwargs.get("url")
    if kwargs.get("image"):
        ret.set_image(url=kwargs.get("image"))
    if kwargs.get("time", kwargs.get("timestamp")):
        ret.timestamp = kwargs.get("time", kwargs.get("timestamp"))
    return ret


class Emol:  # fancy emote-color embeds
    def __init__(self, e: discord.Emoji | str, col: discord.Colour):
        self.emoji = str(e)
        self.color = col

    def con(self, s: str = "", **kwargs):  # constructs
        return construct_embed(title=f"{self.emoji} \u2223 {s}" if s else "", col=self.color, **kwargs)

    async def send(self, destination: discord.abc.Messageable, s: str = None, **kwargs):  # sends
        return await destination.send(embed=self.con(s, **kwargs))

    async def edit(self, message: discord.Message, s: str = None, **kwargs):  # edits message
        return await message.edit(embed=self.con(s, **kwargs))


class ClientEmol(Emol):
    def __init__(self, e: discord.Emoji | str, col: discord.Colour, ctx: commands.Context):
        super().__init__(e, col)
        self.ctx = ctx

    async def say(self, s: str = None, **kwargs):
        return await self.send(self.ctx, s, **kwargs)

    async def resend_if_dm(self, mess: discord.Message, s: str = None, **kwargs):
        if isinstance(self.ctx.channel, discord.DMChannel):
            return await self.say(s, **kwargs)
        else:
            return await self.edit(mess, s, **kwargs)


# IMPORTANT EMOLS
error = Emol(":no_entry:", hex_to_color("880000"))  # error
success = Emol(":white_check_mark:", hex_to_color("22bb00"))  # success
choose = Emol(":8ball:", hex_to_color("e1e8ed"))
wiki = Emol(":globe_with_meridians:", hex_to_color("4100b5"))
phone = Emol(":telephone:", hex_to_color("DD2E44"))
plane = Emol(":airplane:", hex_to_color("3a99f7"))
lost = Emol(":map:", hex_to_color("55ACEE"))  # redirects - looking for these commands?
blue = hex_to_color("3B88C3")  # color that many commands use
