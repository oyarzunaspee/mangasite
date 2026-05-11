from beanie import Document
from enum import Enum
from pydantic import computed_field

class Group(str, Enum):
    yugitachi = "Yugi & Friends"
    memory = "Memory World"
    ishtar = "Ishtar Family"
    antagonists = "Other Antagonists"
    kc = "Kaiba Corp"
    other = "Other"
    duelist = "Duelists"

class Character(Document):
    short: str
    name: str
    eng: str | None
    alt: str | None
    group: str

    @computed_field
    @property
    def grouped(self):
        return Group[self.group].value

    class Settings:
        name = "characters"