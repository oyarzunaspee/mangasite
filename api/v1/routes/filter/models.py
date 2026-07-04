from beanie import Document
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class FilterQueries(BaseModel):
    model_config = {"extra": "forbid"}
    bunkoban:       bool                = False
    saga:           Optional[str]       = None
    arc:            Optional[List[str]] = None
    duel:           Optional[List[str]] = None
    characters:     Optional[List[str]] = None
    page_filters:   Optional[List[str]] = None


class Group(Enum):
    yugitachi =     (1, "Yugi & Friends")
    kc =            (2, "Kaiba Corp")
    ishtar =        (3, "Ishtar Family")
    antagonist =    (4, "Other Antagonists")
    duelist =       (5, "Duelists")
    memory =        (6, "Memory World")

class Character(Document):
    short: str
    name: str
    eng: Optional[str] = None
    alt: Optional[str] = None
    _group: str

    class Settings:
        name = "characters"

    @classmethod
    async def get_groups(cls):
        group_map = {g.name: g.value for g in Group}
        pipeline = [
            {
                "$group": {
                    "_id": "$_group",
                    "characters": {
                        "$push": {
                            "short": "$short",
                            "name": "$name",
                            "eng": "$eng",
                            "alt": "$alt"
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "groupTuple": {
                        "$getField": {
                            "field": "$_id",
                            "input": group_map
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "order": {"$arrayElemAt": ["$groupTuple", 0]},
                    "group": {"$arrayElemAt": ["$groupTuple", 1]}
                }
            },
            {
                "$sort": {
                    "order": 1
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "group": 1,
                    "characters": 1
                }
            }
        ]
            
        chars = await cls.aggregate(pipeline).to_list()
        return chars