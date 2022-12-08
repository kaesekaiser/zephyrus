from fe3h import *


class Tag:
    def __init__(self, owner: User, guild: discord.Guild, id_no: int, name: str, content: str):
        self.owner = owner
        self.guild = guild
        self.id = id_no
        self.name = name
        self.content = content


class TagInterpreter(Interpreter):
    @property
    def tags(self):
        return
