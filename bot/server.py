import asyncio
import discord
import json
import re
from classes.bot import Zeph
from classes.embeds import author_from_user, construct_embed, Emol, success
from classes.interpreter import Interpreter
from classes.menus import Nativity, Navigator, NumSelector, page_list
from discord.ext import commands
from functions import hex_to_color


def abled(b: bool):
    return "Enabled" if b else "Disabled"


class PrefixNavigator(Navigator):
    def __init__(self, bot: Zeph, ctx: commands.Context):
        self.ctx = ctx
        super().__init__(bot, config, self.prefixes, 8, "Custom Prefixes [{page}/{pgs}]", timeout=120)
        self.funcs[self.bot.emojis["no"]] = self.close
        for g in range(self.per):
            self.funcs[f"remove {g+1}"] = partial(self.remove_prefix, g)

    @property
    def prefixes(self):
        return self.bot.server_settings[self.ctx.guild.id].command_prefixes

    @property
    def pgs(self):
        return ceil(len(self.prefixes) / self.per)

    async def remove_prefix(self, n: int):
        try:
            prefix = page_list(self.prefixes, self.per, self.page)[n]
        except IndexError:  # if there aren't that many listed on the page, do nothing
            return

        if len(self.prefixes) == 1:
            await config.edit(self.message, "You can't remove the last prefix.")
            return await asyncio.sleep(2)
        else:
            self.prefixes.remove(prefix)
            await success.edit(self.message, "Prefix removed.")
            if self.page > self.pgs:
                self.page -= 1
            return await asyncio.sleep(2)

    def con(self):
        return self.emol.con(
            self.title.format(page=self.page, pgs=self.pgs),
            d="\n".join(
                f"**`[{g + 1}]`** [`{j}`] - e.g. `{j}help`"
                for g, j in enumerate(page_list(self.prefixes, self.per, self.page))
            ) + "\n\nTo remove a prefix, say `remove <#>` in chat, e.g. `remove 1`. "
                "To completely reset all custom prefixes, exit this menu and use `z!sconfig prefixes reset`."
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
        await self.emol.edit(self.message, "This menu has closed.")
        await self.remove_buttons()


class SelfRoleNavigator(NumSelector):
    def __init__(self, bot: Zeph, roles: list, ctx: commands.Context, mode: str = "view"):
        """mode can be "self", "auto", "assign", or "view". the mode edits the list of selfroles, edits the list of
        autoroles, assigns selfroles to the user, or just browses the list, respectively."""
        super().__init__(bot, config, roles, 8, "Selfroles List", timeout=120, multi=True)
        self.mode = mode
        self.ctx = ctx
        self.user = ctx.author

        if self.mode == "self":
            self.title = "Editing Selfroles"
            self.prefix = f"To set or remove a role as self-assignable, just say the number. " \
                f"{self.bot.emojis['checked']} indicates which roles are currently set as self-assignable. " \
                f"Hit {self.bot.emojis['no']} when you're done.\n\n"
            if self.settings.autoroles:
                self.prefix += f"{self.bot.emojis['checked_autorole']} indicates a role that's already set as " \
                    f"automatically assigned. You can still make this self-assignable if you want.\n\n"
        elif self.mode == "auto":
            self.title = "Editing Autoroles"
            self.prefix = f"To set or remove a role as automatically assigned, just say the number. " \
                f"{self.bot.emojis['checked']} indicates which roles are currently set as automatically assigned. " \
                f"Hit {self.bot.emojis['no']} when you're done.\n\n"
            if self.settings.selfroles:
                self.prefix += f"{self.bot.emojis['checked_selfrole']} indicates a role that's already set as " \
                    f"self-assignable. You can still make this automatically assigned if you want.\n\n"
        elif self.mode == "assign":
            self.title = "Self-Assignable Roles"
            self.prefix = f"To assign or remove a role from yourself, just say the number. " \
                f"{self.bot.emojis['checked']} indicates which roles you currently have. " \
                f"Hit {self.bot.emojis['no']} when you're done.\n\n"
        else:
            self.title = "Self-Assignable Roles"

        self.nativity = Nativity(ctx, block_all=True)
        if self.mode != "view":
            self.bot.nativities.append(self.nativity)
        self.funcs[self.bot.emojis["no"]] = self.close

    @property
    def settings(self):
        return self.bot.server_settings[self.ctx.guild.id]

    async def select(self, n: int):
        role = self.roles_table[n]

        if self.mode == "self":
            if role.id in self.settings.selfroles:
                self.settings.selfroles.remove(role.id)
            else:
                self.settings.selfroles.append(role.id)

        elif self.mode == "auto":
            if role.id in self.settings.autoroles:
                self.settings.autoroles.remove(role.id)
            else:
                self.settings.autoroles.append(role.id)

        elif self.mode == "assign":
            try:
                if role in self.user.roles:
                    await self.user.remove_roles(role, reason="removed via z!selfrole")
                else:
                    await self.user.add_roles(role, reason="added via z!selfrole")
                await asyncio.sleep(0.25)  # to make sure the roles get updated before the menu does
            except discord.Forbidden:  # this shouldn't happen ideally
                raise commands.CommandError("Something went wrong. I can't edit that role.")

    def check(self, role: discord.Role):
        if self.mode == "self":
            if role.id in self.settings.autoroles and role.id not in self.settings.selfroles:
                return self.bot.emojis["checked_autorole"]
            else:
                return self.bot.checked(role.id in self.settings.selfroles)
        elif self.mode == "auto":
            if role.id in self.settings.selfroles and role.id not in self.settings.autoroles:
                return self.bot.emojis["checked_selfrole"]
            else:
                return self.bot.checked(role.id in self.settings.autoroles)
        elif self.mode == "assign":
            return self.bot.checked(role in self.user.roles)

    @property
    def roles_table(self):
        return page_list(self.table, self.per, self.page)

    @property
    def mentions_table(self):
        return "\n".join(
            f"**`{n}.`** {self.check(g)} {g.mention}" if self.mode != "view" else f"- {g.mention}"
            for n, g in enumerate(self.roles_table, 1)
        )

    def con(self):
        return self.emol.con(f"{self.title} [{self.page}/{self.pgs}]", d=self.prefix + self.mentions_table)

    async def close(self):
        self.bot.nativities.remove(self.nativity)
        await self.emol.edit(self.message, "This menu has closed.")
        await self.remove_buttons()


class AitchNavigator(NumSelector):
    def __init__(self, bot: Zeph, ctx: commands.Context):
        super().__init__(bot, config, ctx.guild.text_channels, 8, "Aitch Settings", timeout=120, multi=True)
        self.ctx = ctx
        self.prefix = f"To toggle {self.bot.emojis['aitch']} on or off in a channel, just say the number. " \
            f"{self.bot.emojis['checked']} indicates which channels it is currently enabled in. " \
            f"Hit {self.bot.emojis['no']} when you're done.\n\n"

        self.nativity = Nativity(ctx, block_all=True)
        self.bot.nativities.append(self.nativity)
        self.funcs[self.bot.emojis["no"]] = self.close

    def select(self, n: int):
        channel = self.channels_table[n]

        if channel.id in self.settings.h_exceptions:
            self.settings.h_exceptions.remove(channel.id)
        else:
            self.settings.h_exceptions.append(channel.id)

    @property
    def settings(self):
        return self.bot.server_settings[self.ctx.guild.id]

    def check(self, channel: discord.TextChannel):
        # should show whether or not it's enabled in that channel
        return self.bot.checked(self.settings.h_default ^ (channel.id in self.settings.h_exceptions))

    @property
    def channels_table(self):
        return page_list(self.table, self.per, self.page)

    @property
    def mentions_table(self):
        return "\n".join(f"**`{n}.`** {self.check(g)} {g.mention}" for n, g in enumerate(self.channels_table, 1))

    def con(self):
        return self.emol.con(f"{self.title} [{self.page}/{self.pgs}]", d=self.prefix + self.mentions_table)

    async def close(self):
        self.bot.nativities.remove(self.nativity)
        await self.emol.edit(self.message, "This menu has closed.")
        await self.remove_buttons()


def load_server_settings(zeph: Zeph):
    zeph.server_settings.clear()
    with open("storage/server_settings.json", "r") as f:
        json_dict = json.load(f)

    for g, j in json_dict.items():
        if zeph.get_guild(int(g)):
            zeph.server_settings[int(g)] = ServerSettings(zeph, **j)

    for server in zeph.guilds:
        if server.id not in zeph.server_settings:
            zeph.server_settings[server.id] = ServerSettings.null()


class ServerSettings:
    def __init__(self, bot: Zeph = None, **kwargs):
        if kwargs.get("welcome_channel"):
            self.welcome_channel = bot.get_channel(kwargs.get("welcome_channel"))
        else:
            self.welcome_channel = None
        self.notify_join_enabled = kwargs.pop("notify_join", False)
        self.notify_leave_enabled = kwargs.pop("notify_leave", False)
        self.notify_ban_enabled = kwargs.pop("notify_ban", False)
        self.notify_unban_enabled = kwargs.pop("notify_unban", False)
        self.welcome_message = kwargs.pop("welcome_message", None)

        self.command_prefixes = kwargs.pop("command_prefixes", ["z!"])

        self.autoroles = kwargs.pop("autoroles", [])
        self.autorole_bots = kwargs.pop("autorole_bots", False)
        self.selfroles = kwargs.pop("selfroles", [])

        self.h_default = kwargs.pop("h_default", True)
        self.h_exceptions = kwargs.pop("h_exceptions", [])

        self.sampa = kwargs.pop("sampa", True)

        self.public_emotes = kwargs.pop("public_emotes", True)

    @property
    def notify_join(self):
        return (self.welcome_channel is not None) and self.notify_join_enabled

    @property
    def notify_leave(self):
        return (self.welcome_channel is not None) and self.notify_leave_enabled

    @property
    def notify_ban(self):
        return (self.welcome_channel is not None) and self.notify_ban_enabled

    @property
    def notify_unban(self):
        return (self.welcome_channel is not None) and self.notify_unban_enabled

    @staticmethod
    def null():
        return ServerSettings()

    @property
    def full_json(self):
        return {
            "welcome_channel": self.welcome_channel.id if self.welcome_channel else None,
            "notify_join": self.notify_join_enabled,
            "notify_leave": self.notify_leave_enabled,
            "notify_ban": self.notify_ban_enabled,
            "notify_unban": self.notify_unban_enabled,
            "welcome_message": self.welcome_message,
            "command_prefixes": self.command_prefixes,
            "selfroles": self.selfroles,
            "autoroles": self.autoroles,
            "autorole_bots": self.autorole_bots,
            "h_default": self.h_default,
            "h_exceptions": self.h_exceptions,
            "sampa": self.sampa,
            "public_emotes": self.public_emotes,
        }

    @property
    def minimal_json(self):  # only values which are not the default option
        return {g: j for g, j in self.full_json.items() if self.full_json[g] != ServerSettings.null().full_json[g]}

    @property
    def welcome_fields(self):
        return {
            "Channel": self.welcome_channel.mention if self.welcome_channel else "None",
            "Join Notifications": abled(self.notify_join_enabled),
            "Leave Notifications": abled(self.notify_leave_enabled),
            "Ban Notifications": abled(self.notify_ban_enabled),
            "Unban Notifications": abled(self.notify_unban_enabled)
        }

    def formatted_welcome(self, user: discord.Member):
        if not self.welcome_message:
            return None
        else:
            return self.welcome_message.format(name=user.name)

    def welcome_con(self, user: discord.Member, message: str, col: discord.Color, include_welcome: bool = False):
        return construct_embed(
            title=f"**{user.name}** {message}", d=self.formatted_welcome(user) if include_welcome else None,
            author=author_from_user(user), footer=f"ID: {user.id}", col=col
        )

    async def send_join(self, member: discord.Member):  # if this is changed, update the example in sc welcome message
        await self.welcome_channel.send(embed=self.welcome_con(member, "joined the server!", hex_to_color("22dd22"), True))

    async def send_leave(self, member: discord.Member):
        await self.welcome_channel.send(embed=self.welcome_con(member, "left the server.", hex_to_color("ff8800")))

    async def send_ban(self, member: discord.Member):
        await self.welcome_channel.send(embed=self.welcome_con(member, "has been banned.", hex_to_color("ff0000")))

    async def send_unban(self, member: discord.Member):
        await self.welcome_channel.send(embed=self.welcome_con(member, "has been unbanned.", hex_to_color("2244dd")))

    def can_h_in(self, channel: discord.TextChannel):
        return self.h_default ^ (channel.id in self.h_exceptions)


config = Emol(":gear:", hex_to_color("66757F"))


class SConfigInterpreter(Interpreter):
    redirects = {
        "prefix": "prefixes", "w": "welcome", "p": "prefixes", "selfrole": "selfroles", "sr": "selfroles",
        "autorole": "autoroles", "ar": "autoroles", "h": "help", "x": "sampa", "connie": "sampa", "e": "emotes",
        "emoji": "emotes", "emote": "emotes", "emojis": "emotes"
    }

    @property
    def settings(self):
        return self.bot.server_settings[self.ctx.guild.id]

    async def _help(self, *args: str):
        help_dict = {
            "welcome": "Controls for welcome messages - notifications for when a user joins, leaves, is banned, or "
                       "is unbanned.\n\n"
                       "**`z!sc welcome`** shows the current settings, as well as all controls.\n\n"
                       "`z!sc welcome channel <channel>` sets the channel for welcome messages.\n\n"
                       "`z!sc welcome enable <join | leave | ban | unban | all>` enables types of notifications.\n\n"
                       "`z!sc welcome disable <join | leave | ban | unban | all>` disables types of notifications.\n\n"
                       "**`z!sc welcome message`** shows the current custom welcome message, and all controls.\n\n"
                       "`z!sc welcome message set <message...>` sets a new custom welcome message.\n\n"
                       "`z!sc welcome message remove` removes the current welcome message.",
            "prefixes": "Controls for custom command prefixes.\n\n"
                        "**`z!sc prefixes`** shows the currently enabled prefixes, and all controls.\n\n"
                        "`z!sc prefix add <prefix>` adds a new prefix.\n\n"
                        "`z!sc prefix remove <prefix>` removes a prefix.\n\n"
                        "`z!sc prefixes reset` removes all custom prefixes and resets to the default, `z!`.",
            "selfroles": "Controls for self-assignable roles.\n\n"
                         "**`z!sc selfroles`** shows detailed selfrole information, as well as all controls.\n\n"
                         "`z!sc selfroles edit` allows you to set and un-set specific roles as self-assignable.\n\n"
                         "`z!sc selfroles clear` turns off all selfroles.",
            "autoroles": "Controls for automatically-assigned roles.\n\n"
                         "**`z!sc autoroles`** shows detailed autorole information, as well as all controls.\n\n"
                         "`z!sc autoroles edit` allows you to set and un-set specific roles as auto-assigned.\n\n"
                         "`z!sc autoroles reassign` automatically reassigns all autoroles to all current members.\n\n"
                         "`z!sc autoroles clear` turns off all autoroles.\n\n"
                         "`z!sc autoroles bots <enable | disable>` sets whether to give autoroles to bots.",
            "aitch": f"Controls for Zeph's {self.bot.emojis['aitch']} feature.\n\n"
                     f"**`z!sc aitch`** shows the current settings, as well as all controls.\n\n"
                     f"`z!sc aitch enable/disable all` enables or disables the function in all channels at once.\n\n"
                     f"`z!sc aitch channels` allows you to enable or disable the function in specific channels.",
            "sampa": "Controls for Zeph's X- and Z-SAMPA interpretation feature.\n\n"
                     "**`z!sc sampa`** shows the current settings, as well as all controls.\n\n"
                     "`z!sc sampa enable/disable` enables or disables the feature.",
            "emotes": "Privacy settings for the global use of emotes via `z!emote`.\n\n"
                      "**`z!sc emotes`** shows the current settings, as well as all controls.\n\n"
                      "`z!sc emotes public/private` sets the server's emotes to publicly available or private."
        }
        desc_dict = {
            "welcome": "Controls for welcome messages.",
            "prefixes": "Controls for custom command prefixes.",
            "selfroles": "Controls for self-assignable roles.",
            "autoroles": "Controls for automatically-assigned roles.",
            "aitch": f"Controls for Zeph's {self.bot.emojis['aitch']} feature.",
            "sampa": "Controls for Zeph's X- and Z-SAMPA interpretation feature.",
            "emotes": "Controls for Zeph's global emote use feature."
        }

        if len(args) == 0 or (args[0].lower() not in help_dict and args[0].lower() not in self.redirects):
            return await config.send(
                self.ctx, "z!sconfig help",
                d="Available functions:\n\n" + "\n".join(f"`{g}` - {j}" for g, j in desc_dict.items()) +
                "\n\nFor information on how to use these, use `z!sconfig help <function>`.\n"
                "(more functions will be added in the future!)"
            )

        ret = self.redirects.get(args[0].lower(), args[0].lower())

        return await config.send(self.ctx, f"z!sconfig {ret}", d=help_dict[ret])

    async def _welcome(self, *args: str):
        if not args:
            return await config.send(
                self.ctx, "Welcome Message Options",
                d="To enable/disable specific types of notifications:\n`z!sconfig welcome enable/disable <x>`\n"
                  "To enable/disable all notifications at once:\n`z!sconfig welcome enable/disable all`\n"
                  "To change the channel in which notifications are sent:\n`z!sconfig welcome channel <channel>`\n"
                  "To view custom welcome message settings:\n`z!sconfig welcome message`" +
                  ("\n\n**No notifications will be sent until the welcome channel is set.**"
                   if not self.settings.welcome_channel else ""),
                fs=self.settings.welcome_fields,
                same_line=True
            )

        if args[0].lower() == "channel":
            if len(args) == 1:
                return await config.send(
                    self.ctx,
                    f"The welcome channel is currently set to #{self.settings.welcome_channel.name}."
                    if self.settings.welcome_channel else "The welcome channel is not set yet.",
                    d="To change this, use `z!sconfig welcome channel <new channel>`."
                )

            try:
                channel = await commands.TextChannelConverter().convert(self.ctx, args[1])
            except commands.BadArgument:
                raise commands.CommandError(f"Channel `{args[1]}` not found.")
            else:
                self.settings.welcome_channel = channel
                return await success.send(
                    self.ctx, "Welcome channel set.", d=f"Traffic notifications will now be sent to {channel.mention}."
                )

        elif args[0].lower() == "enable":
            if len(args) == 1:
                raise commands.CommandError("Format: `z!sconfig welcome enable <type>`")

            warning = None if self.settings.welcome_channel else \
                "Notifications will not be sent until the welcome channel is set. " \
                "Use `z!sconfig welcome channel <channel>` to set one."

            if args[1].lower() == "all":
                self.settings.notify_join_enabled = True
                self.settings.notify_leave_enabled = True
                self.settings.notify_ban_enabled = True
                self.settings.notify_unban_enabled = True
                return await success.send(self.ctx, "All traffic notifications **enabled**.", d=warning)

            elif args[1].lower() in ["join", "leave", "ban", "unban"]:
                if args[1].lower() == "join":
                    if self.settings.notify_join_enabled:
                        return await config.send(self.ctx, "Join notifications are already enabled.", d=warning)
                    self.settings.notify_join_enabled = True
                if args[1].lower() == "leave":
                    if self.settings.notify_leave_enabled:
                        return await config.send(self.ctx, "Leave notifications are already enabled.", d=warning)
                    self.settings.notify_leave_enabled = True
                if args[1].lower() == "ban":
                    if self.settings.notify_ban_enabled:
                        return await config.send(self.ctx, "Ban notifications are already enabled.", d=warning)
                    self.settings.notify_ban_enabled = True
                if args[1].lower() == "unban":
                    if self.settings.notify_unban_enabled:
                        return await config.send(self.ctx, "Unban notifications are already enabled.", d=warning)
                    self.settings.notify_unban_enabled = True

                return await success.send(self.ctx, f"{args[1].title()} notifications **enabled**.", d=warning)

            else:
                raise commands.CommandError(f"Invalid argument `{args[1]}`.")

        elif args[0].lower() == "disable":
            if len(args) == 1:
                raise commands.CommandError("Format: `z!sconfig welcome disable <type>`")

            if args[1].lower() == "all":
                self.settings.notify_join_enabled = False
                self.settings.notify_leave_enabled = False
                self.settings.notify_ban_enabled = False
                self.settings.notify_unban_enabled = False
                return await success.send(self.ctx, "All traffic notifications **disabled**.")

            elif args[1].lower() in ["join", "leave", "ban", "unban"]:
                if args[1].lower() == "join":
                    if not self.settings.notify_join_enabled:
                        return await config.send(self.ctx, "Join notifications are already disabled.")
                    self.settings.notify_join_enabled = False
                if args[1].lower() == "leave":
                    if not self.settings.notify_leave_enabled:
                        return await config.send(self.ctx, "Leave notifications are already disabled.")
                    self.settings.notify_leave_enabled = False
                if args[1].lower() == "ban":
                    if not self.settings.notify_ban_enabled:
                        return await config.send(self.ctx, "Ban notifications are already disabled.")
                    self.settings.notify_ban_enabled = False
                if args[1].lower() == "unban":
                    if not self.settings.notify_unban_enabled:
                        return await config.send(self.ctx, "Unban notifications are already disabled.")
                    self.settings.notify_unban_enabled = False

                return await success.send(self.ctx, f"{args[1].title()} notifications **disabled**.")

            else:
                raise commands.CommandError(f"Invalid argument `{args[1]}`.")

        elif args[0].lower() == "message":
            if len(args) == 1:
                return await config.send(
                    self.ctx, "Welcome Message Settings",
                    d="The welcome message is an optional custom text that will be displayed alongside the "
                    "notification for a new member joining the server.\n\n"
                    "To set a new welcome message:\n`z!sconfig welcome message set <message...>`\n"
                    "To remove the welcome message:\n`z!sconfig welcome message remove`\n\n"
                    "When writing a welcome message, you can include the string **`{name}`**, and it will be replaced "
                    "with the user's name - `z!sc welcome message set Welcome, {name}!` will become \"Welcome, Fort!\"",
                    fs={"Current Welcome Message": self.settings.welcome_message}
                )

            if args[1].lower() == "set":
                message = " ".join(args[2:])

                if not message:
                    raise commands.CommandError("Cannot have an empty welcome message.")

                if len(message) > 1024:
                    raise commands.CommandError("The welcome message can't be more than 1024 characters long.")

                if await self.bot.confirm(
                    "Set the welcome message?", self.ctx, self.au,
                    add_info="This will look like:\n\n" + message.format(name=self.au.name) + "\n\n"
                ):
                    self.settings.welcome_message = message
                    return await success.send(self.ctx, "Welcome message set.")
                else:
                    return await config.send(self.ctx, "Welcome message settings were not changed.")

            elif args[1].lower() == "remove":
                if await self.bot.confirm(
                    "Remove the welcome message?", self.ctx, self.au,
                    add_info="This will **not** disable the join notification; it will just reset it to the default."
                ):
                    self.settings.welcome_message = None
                    return await success.send(self.ctx, "Welcome message removed.")
                else:
                    return await config.send(self.ctx, "Welcome message settings were not changed.")

            else:
                raise commands.CommandError(f"Invalid argument `{args[1]}`.")

        else:
            raise commands.CommandError(f"Invalid argument `{args[0]}`.")

    async def _prefixes(self, *args: str):
        if not args:
            prefix_preview = "\n".join(f"[`{g}`] - e.g. `{g}help`" for g in self.settings.command_prefixes[:5]) + \
                (f"\n...plus **{len(self.settings.command_prefixes) - 5}** more; see `z!sc prefixes list`"
                 if len(self.settings.command_prefixes) > 5 else "")
            return await config.send(
                self.ctx, "Custom Command Prefixes",
                d="To add a prefix:\n`z!sconfig prefix add \"<prefix>\"`\n"
                  "To view and disable prefixes:\n`z!sconfig prefixes list`\n"
                  "To reset to only the default prefix, `z!`:\n`z!sconfig prefixes reset`\n\n"
                  "Please enclose the **entire prefix** in \"double quotes\" when adding or removing, especially if "
                  "the prefix includes a trailing space.",
                fs={"Current Prefixes": prefix_preview}
            )

        if args[0].lower() == "add":
            if len(args) == 1:
                raise commands.CommandError("Format: `z!sconfig prefix add \"<prefix>\"`")

            if len(args) > 2:
                raise commands.CommandError("Please enclose the entire prefix in \"double quotes\".")

            prefix = args[1]

            if len(prefix) > 100:
                raise commands.CommandError("Prefixes cannot be more than 100 characters long.")

            warning = f"This will look like: **`{prefix}help`** or **`{prefix}sconfig prefixes reset`**.\n"

            if not prefix:
                raise commands.CommandError("Cannot have an empty prefix.")

            if re.match(r"\s", prefix):
                # discord removes leading whitespaces, so a prefix that starts with a space would be unusable
                raise commands.CommandError("Prefixes cannot begin with a whitespace.")

            if prefix in self.settings.command_prefixes:
                raise commands.CommandError("That prefix is already enabled.")

            for existing_prefix in self.settings.command_prefixes:
                if prefix in existing_prefix and existing_prefix.index(prefix) == 0:
                    warning += f"\n:rotating_light: **WARNING:** This will **overwrite and remove** the existing " \
                        f"prefix `{existing_prefix}`, which contains `{prefix}`.\n"

            if await self.bot.confirm(f"Add the prefix `{prefix}`?", self.ctx, self.au, add_info=warning+"\n"):
                extra_info = ""
                for existing_prefix in self.settings.command_prefixes:
                    if prefix in existing_prefix and existing_prefix.index(prefix) == 0:
                        self.settings.command_prefixes.remove(existing_prefix)
                        extra_info += f"Prefix `{existing_prefix}` removed.\n"

                self.settings.command_prefixes.append(prefix)
                return await success.send(self.ctx, f"Prefix `{prefix}` added.", d=extra_info)

            else:
                return await config.send(self.ctx, "Prefixes were not changed.")

        elif args[0].lower() in ["edit", "list"]:
            return await PrefixNavigator(self.bot, self.ctx).run(self.ctx)

        elif args[0].lower() == "remove":
            if len(args) == 1:
                raise commands.CommandError("Format: `z!sconfig prefix remove \"<prefix>\"`")

            if len(args) > 2:
                raise commands.CommandError("Please enclose the entire prefix in \"double quotes\".")

            prefix = args[1]

            if prefix not in self.settings.command_prefixes:
                raise commands.CommandError(f"Prefix `{prefix}` not found.")

            if len(self.settings.command_prefixes) == 1:
                raise commands.CommandError("You can't remove the only enabled command prefix.")

            if await self.bot.confirm(f"Remove the prefix `{prefix}`?", self.ctx, self.au):
                self.settings.command_prefixes.remove(prefix)
                return await success.send(self.ctx, "Prefix removed.")

            else:
                return await config.send(self.ctx, "Prefixes were not changed.")

        elif args[0].lower() == "reset":
            warning = f"This will remove all custom prefixes" \
                f"{', leaving only' if 'z!' in self.settings.command_prefixes else ' and re-enable'} " \
                f"the default prefix `z!`."

            if await self.bot.confirm("Reset custom prefixes?", self.ctx, self.au, add_info=warning):
                self.settings.command_prefixes.clear()
                self.settings.command_prefixes.append("z!")
                return await success.send(self.ctx, "Prefixes reset.")

            else:
                return await config.send(self.ctx, "Prefixes were not changed.")

        else:
            raise commands.command(f"Invalid argument `{args[0]}`.")

    async def _selfroles(self, *args: str):
        if not args:
            return await config.send(
                self.ctx, "Selfrole Settings",
                d="Selfroles are roles that any server member can assign themselves using the `z!selfroles` menu.\n\n"
                  "To view and edit enabled selfroles:\n`z!sc selfroles edit`\n"
                  "To remove all selfroles:\n`z!sc selfroles clear`\n\n"
                  "Some roles may not show up in the list. In order for a role to be self-assignable, it must be "
                  "**lower than Zephyrus's top role** - otherwise, Zephyrus won't be able to assign it." +
                  (" :rotating_light: Currently, there are **no roles which fit this criteria**, so "
                   "**no roles can be set**." if not self.bot.sorted_assignable_roles(self.ctx.guild) else "") +
                  ("\n\n:rotating_light: **NOTE:** Zephyrus needs the **Manage Roles** permission for selfrole "
                   "functionality." if not self.ctx.guild.me.guild_permissions.manage_roles else "")
            )

        if args[0].lower() == "edit":
            if not self.ctx.guild.me.guild_permissions.manage_roles:
                raise commands.CommandError("I need the **Manage Roles** permission to assign selfroles.")

            if not self.bot.sorted_assignable_roles(self.ctx.guild):
                return await config.send(
                    self.ctx, "There are no roles that I can assign. See `z!sc selfroles` for more info."
                )

            return await SelfRoleNavigator(self.bot, self.bot.sorted_assignable_roles(self.ctx.guild),
                                           self.ctx, "self").run(self.ctx)

        elif args[0].lower() == "clear":
            if not self.bot.server_settings[self.ctx.guild.id].selfroles:
                return await config.send(self.ctx, "There are no selfroles to clear.")

            if await self.bot.confirm(
                f"Disable all {len(self.settings.selfroles)} selfroles?", self.ctx, self.au,
                add_info="This will *not* remove any roles from members who already have them, but will prevent "
                         "members from self-assigning these roles unless re-enabled.\n\n"
            ):
                self.settings.selfroles.clear()
                return await success.send(self.ctx, "Selfroles cleared.")

            else:
                return await config.send(self.ctx, "Selfroles were not changed.")

        else:
            raise commands.CommandError(f"Invalid argument `{args[0]}`.")

    async def _autoroles(self, *args: str):
        if not args:
            return await config.send(
                self.ctx, "Autorole Settings",
                d="Autoroles are roles that are automatically assigned to all new members of the server.\n\n"
                  "To view and edit the list of autoroles:\n`z!sc autoroles edit`\n"
                  "To automatically re-assign all autoroles to each server member (use this if you add a new "
                  "autorole):\n`z!sc autoroles reassign`\n"
                  "To toggle whether to give autoroles to bots (disabled by default):\n"
                  "`z!sc autoroles bots enable/disable`\n"
                  "To clear all autoroles:\n`z!sc autoroles clear`\n\n"
                  "Some roles may not show up in the list. In order for a role to be automatically assigned, it must "
                  "be **lower than Zephyrus's top role** - otherwise, Zephyrus won't be able to assign it." +
                  (" :rotating_light: Currently, there are **no roles which fit this criteria**, so "
                   "**no roles can be set**." if not self.bot.sorted_assignable_roles(self.ctx.guild) else "") +
                  ("\n\n:rotating_light: **NOTE:** Zephyrus needs the **Manage Roles** permission for autorole "
                   "functionality." if not self.ctx.guild.me.guild_permissions.manage_roles else ""),
                fs={"Give autoroles to bots?": abled(self.bot.server_settings[self.ctx.guild.id].autorole_bots)}
            )

        elif args[0].lower() == "edit":
            if not self.ctx.guild.me.guild_permissions.manage_roles:
                raise commands.CommandError("I need the **Manage Roles** permission to assign autoroles.")

            if not self.bot.sorted_assignable_roles(self.ctx.guild):
                return await config.send(
                    self.ctx, "There are no roles that I can assign. See `z!sc autoroles` for more info."
                )

            return await SelfRoleNavigator(self.bot, self.bot.sorted_assignable_roles(self.ctx.guild),
                                           self.ctx, "auto").run(self.ctx)

        elif args[0].lower() == "reassign":
            if not self.ctx.guild.me.guild_permissions.manage_roles:
                raise commands.CommandError("I need the **Manage Roles** permission to assign roles.")

            if not self.settings.autoroles:
                return await config.send(self.ctx, "There are no autoroles to assign.")

            def check(u: discord.Member):
                if not (set(self.settings.autoroles) <= {g.id for g in u.roles}):
                    if u.bot and not self.settings.autorole_bots:
                        return False
                    else:
                        return True
                return False

            users = list(filter(check, self.ctx.guild.members))

            if not users:
                return await success.send("All members are currently up-to-date on autoroles.")

            mess = await Emol(self.bot.emojis["loading"], hex_to_color("66757F"))\
                .send(self.ctx, f"Updating roles for {len(users)} members...")
            roles = [self.ctx.guild.get_role(g) for g in self.settings.autoroles]
            for user in users:
                await user.add_roles(*roles, reason="re-assigning autoroles")

            return await success.edit(mess, "Autoroles re-assigned.")

        elif args[0].lower() == "bots":
            if len(args) == 1:
                return await config.send(
                    self.ctx,
                    f"Currently, bots {'**are**' if self.settings.autorole_bots else 'are **not**'} given autoroles.",
                    d=f"To change this, use `z!sc autoroles bots {abled(not self.settings.autorole_bots).lower()[:-1]}"
                      f"`. By default, bots are **not** given autoroles."
                )

            if args[1].lower() == "enable":
                if self.settings.autorole_bots:
                    return await config.send(self.ctx, "Bots are already given autoroles.")
                else:
                    self.settings.autorole_bots = True
                    return await success.send(
                        self.ctx, "Bots will now be given autoroles.",
                        d="Use `z!sc autoroles reassign` to update all present bots with the autoroles, automatically."
                    )

            elif args[1].lower() == "disable":
                if not self.settings.autorole_bots:
                    return await config.send(self.ctx, "Bots are already not given autoroles.")
                else:
                    self.settings.autorole_bots = False
                    return await success.send(self.ctx, "Bots will no longer be given autoroles.")

            else:
                raise commands.CommandError(f"Invalid argument `{args[1]}`.")

        elif args[0].lower() == "clear":
            if not self.bot.server_settings[self.ctx.guild.id].autoroles:
                return await config.send(self.ctx, "There are no autoroles to clear.")

            if await self.bot.confirm(
                f"Disable all {len(self.settings.autoroles)} autoroles?", self.ctx, self.au,
                add_info="This will *not* remove any roles from members who already have them, but will stop roles "
                         "from being automatically added to new members.\n\n"
            ):
                self.settings.autoroles.clear()
                return await success.send(self.ctx, "Autoroles cleared.")

            else:
                return await config.send(self.ctx, "Autoroles were not changed.")

        else:
            raise commands.CommandError(f"Invalid argument `{args[0]}`.")

    async def _aitch(self, *args: str):
        if not args:
            exceptions = sorted([self.bot.get_channel(g) for g in self.settings.h_exceptions], key=lambda c: c.position)
            if exceptions:
                embed_fs = {
                    "Default": f"{self.bot.emojis['aitch']} is currently **{abled(self.settings.h_default).lower()}** in "
                    f"most channels, and will be initially {abled(self.settings.h_default).lower()} in new channels.",
                    "Exceptions": f"{self.bot.emojis['aitch']} is currently **{abled(not self.settings.h_default).lower()}"
                    f"** in **{len(exceptions)} {plural('channel', len(exceptions))}:** "
                    f"{', '.join(g.mention for g in exceptions[:10])}"
                    + (f", and **{round(len(exceptions) - 10)}** more" if len(exceptions) > 10 else "")
                }
            else:
                embed_fs = {
                    "Default": f"{self.bot.emojis['aitch']} is currently **{abled(self.settings.h_default).lower()}** in "
                    f"**all channels**, and will be initially {abled(self.settings.h_default).lower()} in new channels."
                }

            return await config.send(
                self.ctx, "Aitch Settings",
                d="Zephyrus will respond with " + self.bot.strings["aitch"] +
                  " to messages consisting of solely `h`. This is on by default, but can be disabled.\n\n"
                  "To enable or disable across all channels at once:\n`z!sc aitch enable/disable`\n"
                  "To enable or disable on a channel-by-channel basis:\n`z!sc aitch channels`",
                fs=embed_fs
            )

        elif args[0].lower() == "enable":
            if self.settings.h_default is True:
                if self.settings.h_exceptions:
                    self.settings.h_exceptions.clear()
                    return await success.send(self.ctx, f"{self.bot.emojis['aitch']} enabled in all channels.")
                else:
                    return await config.send(self.ctx, f"{self.bot.emojis['aitch']} is already enabled in all channels.")
            else:
                self.settings.h_default = True
                self.settings.h_exceptions.clear()
                return await success.send(self.ctx, f"{self.bot.emojis['aitch']} enabled in all channels.")

        elif args[0].lower() == "disable":
            if self.settings.h_default is False:
                if self.settings.h_exceptions:
                    self.settings.h_exceptions.clear()
                    return await success.send(self.ctx, f"{self.bot.emojis['aitch']} disabled in all channels.")
                else:
                    return await config.send(self.ctx, f"{self.bot.emojis['aitch']} is already disabled in all channels.")
            else:
                self.settings.h_default = False
                self.settings.h_exceptions.clear()
                return await success.send(self.ctx, f"{self.bot.emojis['aitch']} disabled in all channels.")

        elif args[0].lower() in ["channel", "channels"]:
            return await AitchNavigator(self.bot, self.ctx).run(self.ctx)

        else:
            raise commands.CommandError(f"Invalid argument `{args[0]}`.")

    async def _sampa(self, *args: str):
        if not args:
            return await config.send(
                self.ctx, "SAMPA Settings",
                d=f"In the style of the late Connie bot, Zephyrus will automatically interpret X-SAMPA text surrounded "
                  f"by x/slashes/ or x[brackets] preceded by a lowercase `x`, and Z-SAMPA text in z/slashes/ or "
                  f"z[brackets] preceded by a lowercase `z`. This is on by default, but can be disabled.\n\n"
                  f"To enable or disable:\n`z!sc sampa enable/disable`\n\n"
                  f"SAMPA interpretation is currently **{abled(self.settings.sampa).lower()}**."
            )

        elif args[0].lower() == "disable":
            if not self.settings.sampa:
                return await config.send(self.ctx, "SAMPA interpretation was already disabled.")
            else:
                self.settings.sampa = False
                return await success.send(self.ctx, "SAMPA interpretation disabled.")

        elif args[0].lower() == "enable":
            if self.settings.sampa:
                return await config.send(self.ctx, "SAMPA interpretation was already enabled.")
            else:
                self.settings.sampa = True
                return await success.send(self.ctx, "SAMPA interpretation enabled.")

        else:
            raise commands.CommandError(f"Invalid argument `{args[0]}`.")

    async def _emotes(self, *args: str):
        if not args:
            meaning = "they **can be accessed anywhere** through `z!e` and **are included** in `z!esearch` results" \
                if self.settings.public_emotes else \
                "they **cannot be accessed** through `z!e` and **are not included** in `z!esearch results`"
            return await config.send(
                self.ctx, "Emote Privacy Settings",
                d="Discord bots have the ability to use any custom emoji from any server of which they are a member, "
                  "in any other server. Zephyrus takes advantage of this feature using the commands `z!emoji` and "
                  "`z!react` to allow users to display or react with an emoji from a different server. If a server's "
                  "emotes are set to public, the emotes and their names may be seen through the use of `z!emoji` and "
                  "`z!esearch` in other servers. The server's name is not displayed.\n\n"
                  "Emotes are public by default, but may be made private at any time.\n\n"
                  "To change settings:\n`z!sc emotes public/private`\n\n"
                  f"This server's emotes are currently **{'public' if self.settings.public_emotes else 'private'}**, "
                  f"meaning {meaning}."
            )

        elif args[0].lower() == "public":
            if self.settings.public_emotes:
                return await config.send(self.ctx, "This server's emotes were already public.")
            else:
                self.settings.public_emotes = True
                return await success.send(self.ctx, "This server's emotes are now accessible through `z!e`.")

        elif args[0].lower() == "private":
            if self.settings.public_emotes:
                self.settings.public_emotes = False
                return await success.send(self.ctx, "This server's emotes are no longer accessible through `z!e`.")
            else:
                return await config.send(self.ctx, "This server's emotes were already private.")


class ServerSettingsCog(commands.Cog):
    def __init__(self, bot: Zeph):
        self.bot = bot

    @commands.command(
        aliases=["sc"], usage="z!sconfig help",
        description="Server configuration options.",
        help="**Admin command.** Allows you to view and change various server configuration options, such as join/leave "
             "messages, custom prefixes, etc. Use `z!sconfig help` for more specific details."
    )
    async def sconfig(self, ctx: commands.Context, func: str = None, *args: str):
        if not ctx.guild:
            raise commands.CommandError("This command can only be run in a server.")

        if not ctx.author.guild_permissions.manage_guild:
            raise commands.CommandError("You don't have permission to do that.")

        if not func:
            return await config.send(
                ctx, "Server Configuration",
                d="This command allows you to edit Zephyrus's various server configuration options, like welcome messages, "
                  "custom prefixes, etc. Use `z!sconfig help` for more info."
            )

        return await SConfigInterpreter(self.bot, ctx).run(func, *args)

    @commands.command(
        name="selfroles", aliases=["sr", "selfrole", "roles"], usage="z!selfroles",
        description="Allows you to edit your self-assigned roles.",
        help="Allows you to browse the server's list of self-assigned roles, and assign them to or remove them from "
             "yourself via a menu."
    )
    async def selfroles_command(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.CommandError("This command can only be run in a server.")

        if not ctx.guild.me.guild_permissions.manage_roles:
            return await config.send(
                ctx, "Selfroles are not configured for this server.",
                d="If you're an admin, see `z!sc selfroles` for more info."
            )

        if not self.bot.sorted_assignable_roles(ctx.guild, True):
            return await config.send(ctx, "This server has no self-assigned roles.")

        return await SelfRoleNavigator(self.bot, self.bot.sorted_assignable_roles(ctx.guild, True),
                                       ctx, "assign").run(ctx)
