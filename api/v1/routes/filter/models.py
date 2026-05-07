from beanie import Document, Link

class Character(Document):
    short: str
    name: str
    eng: str | None
    alt: Link["Character"] | None

    class Settings:
        name = "characters"