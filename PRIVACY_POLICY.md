# Privacy Policy
This document describes in full detail what data the Discord bot distributed by the author (hereafter referred to as Zephyrus) collects and stores long-term, as well as how to delete said data.
## What Zephyrus Doesn't Store
Under normal circumstances, Zephyrus does not store any usernames, server names, names for server attributes such as channels or emotes, or message content, unless explicitly provided by the user via the use of its commands as described below.
## What Zephyrus Stores
Zephyrus's data is stored entirely in terms of "snowflake" identifiers provided by the Discord API. These snowflakes consist solely of a single unsigned integer, and may represent users, servers, channels, channel categories, messages, emotes, server roles, group DMs, or threads. They are not encrypted, and there is no meaningful connection between a snowflake and the object it represents: that is, all Zephyrus sees is a meaningless number.
Zephyrus stores several of these snowflakes for various reasons, each of which is associated with a specific command. Some of these commands also store user-generated content provided therein. Each command for which Zephyrus stores data is described below.
### `z!planes`
When a user creates a zPlanes profile through the use of `z!planes new`, Zephyrus stores their snowflake. Each snowflake is keyed to data representing the in-game data for that user's profile (e.g. owned cities and licenses), which includes the text of user-generated plane names.
### `z!remindme`
When a user sets a reminder through the use of `z!remindme`, Zephyrus stores their snowflake, the text of that reminder, and a timestamp representing the time that reminder will be sent.
### `z!sconfig`
Zephyrus stores the snowflake of each server it is in. Each snowflake is keyed to data representing the user-configured server settings for the associated server, including the text of custom command prefixes and welcome messages, and the snowflakes of autoroles or selfroles. If `z!sconfig` has never been used to change the settings of a server, or if settings have been restored to their default values, no data is stored.
## What The Author Receives
* The author sees any text provided through the `z!feedback` command in full, as well as the snowflakes of the user, message, and server.
* For debugging purposes, Zephyrus displays to the author the server and message snowflakes, and the full message text, when any error is encountered in the software itself - i.e., when a Python error like a `ValueError` is encountered. This does not include user input errors. Such errors are encountered extraordinarily rarely, and are distinguished on the user's end via the preface "`Command encountered an error: `".
## How to Remove Your Data
All Zephyrus data can be managed through the bot itself.
* To delete data associated with the `z!planes` command, use `z!planes restart`. Zephyrus will delete all saved data, including the snowflake of the user.
* To delete data associated with the `z!remindme` command, use the "remove" function provided by the `z!remindme list` menu. Zephyrus will delete the user snowflake, reminder text, and timestamp of any reminder removed via that menu. See that command for full instructions.
* To delete data associated with the `z!sconfig` command, use the reset functions provided by the various sub-commands by calling those commands in a channel in the server whose data you'd like to delete. Use `z!sconfig help` for full instructions. Zephyrus immediately deletes the server configuration settings for, and the snowflake of, any server which it leaves or is kicked from.
