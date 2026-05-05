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

class Chapter(Document):
    number: int
    title: str
    arc: str
    characters: List[str]
    duel: str | None
    jpn: str

    class Settings:
        name = "chapters"


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

    @classmethod
    async def query_volumes(cls, bunkoban: bool = False, saga: str = None) -> List["Chapter"]:

        match = {
            "volume.bunkoban": bunkoban
        }

        if saga:
            match["volume.saga"] = saga
        
        pipeline = [
            {
                "$lookup": {
                    "from": Volume.get_collection_name(),
                    "localField": "volume.$id",
                    "foreignField": "_id",
                    "as": "volume"
                }
            },
            {"$unwind": "$volume"},
            {
                "$match": match
            },
            {
                "$lookup": {
                    "from": Chapter.get_collection_name(),
                    "localField": "chapter.$id",
                    "foreignField": "_id",
                    "as": "chapter"
                }
            },
            {"$unwind": "$chapter"},
            {
                "$group": {
                    "_id": "$chapter._id",
                    "title": {"$first": "$chapter.title"},
                    "number": {"$first": "$chapter.number"},
                    "jpn": {"$first": "$chapter.jpn"},
                    "volume": {"$first": "$volume"}
                }
            },
            {
                "$sort": {"number": 1}
            },
            {
                "$group": {
                    "_id": "$volume._id",
                    "volume": {"$first": "$volume"},
                    "chapters": {
                        "$push": {
                            "number": "$number",
                            "title": "$title",
                            "jpn": "$jpn"
                        }
                    }
                }
            },
            {
                "$sort": {
                    "volume.counter": 1
                }
            },
            {
                "$set": {
                    "first_chapter": { "$first": "$chapters" }
                }
            },
            {
                "$lookup": {
                    "from": Page.get_collection_name(),
                    "localField": "volume._id",
                    "foreignField": "volume.$id",
                    "as": "pages"
                }
            },
            {
                "$set": {
                    "cover_page": {
                        "$first": {
                            "$filter": {
                                "input": "$pages",
                                "as": "p",
                                "cond": {"$eq": ["$$p.volume_cover", True]}
                            }
                        }
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "counter": "$volume.counter",
                    "title": "$volume.title",
                    "cover": {
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
                            {
                                "$toString": {
                                    "$ifNull": ["$first_chapter.number", 0]
                                }
                            },
                            "_",
                            {
                                "$toString": {
                                    "$ifNull": ["$cover_page.number", 0]
                                }
                            },
                            ".png"
                        ]
                    },
                    "chapters": 1
                }
            }
        ]

        chapters = await cls.aggregate(pipeline).to_list()

        return chapters
    
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