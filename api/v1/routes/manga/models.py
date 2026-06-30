from pydantic import computed_field, BaseModel
from beanie import Document, Link
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

URL = os.getenv("STORE_URL")

class Volume(Document):
    number: int
    title: str
    bunkoban: bool = False
    saga: str | None
    counter: int

    class Settings:
        name = "volumes"

class Arc(BaseModel):
    name: str
    number: int

class Chapter(Document):
    number: int
    title: str
    arc: Arc | None
    characters: List[str]
    duel: str | None
    jpn: str

    class Settings:
        name = "chapters"

    @classmethod
    async def get_arc_values(cls):
        pipeline = [
            {"$match": {"arc": {"$ne": None}}},
            {"$sort": {"number": 1}},
            {
                "$group": {
                    "_id": "$arc"
                }
            },
            {
                "$group": {
                    "_id": None,
                    "arcs": {"$push": "$_id"}
                }
            },
            {"$project": {"_id": 0, "arcs": 1}}
                ]
        arcs = await cls.aggregate(pipeline).to_list()
        return arcs

class Page(Document):
    volume: Link[Volume]
    chapter: Link[Chapter]
    number: int
    volume_cover: bool
    chapter_cover: bool
    author_notes: bool
    tarot: bool
    extra_illust: bool
    game: bool
    double: bool
    content: bool
    image: str

    class Settings:
        name = "pages"
        page_filters = [
            {
                "query": "volume_cover",
                "name": "Volume covers"
            },
            {
                "query": "chapter_cover",
                "name": "Chapter covers"
            },
            {
                "query": "author_notes",
                "name": "Takahashi's author notes"
            },
            {
                "query": "tarot",
                "name": "Tarot covers and notes"
            },
            {
                "query": "extra_illust",
                "name": "Extra illustrations"
            },
            {
                "query": "game",
                "name": "Game pages"
            }
        ]

    @classmethod
    async def query_volumes(cls, pipeline) -> List["Chapter"]:
        volumes = await cls.aggregate(pipeline).to_list()

        return volumes
    
    
class IndividualPages(BaseModel):
    number: int
    link: str
    double: bool
    content: bool

    class Settings:
        projection = {
            "number": 1, 
            "double": 1,
            "content": 1,
            "link": {
                "$concat": [
                    URL,
                    {
                        "$cond": [
                            "$volume.bunkoban",
                            "bunkoban",
                            "og"
                        ]
                    },
                    "_",
                    {"$toString": "$volume.counter"},
                    "_",
                    {"$toString": "$chapter.number"},
                    "_",
                    {"$toString": "$number"},
                    ".png"
                ]
            }
        }