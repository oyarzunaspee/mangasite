from beanie import Document, Link

class Character(Document):
    short: str
    name: str
    eng: str | None
    alt: str | None

    class Settings:
        name = "characters"