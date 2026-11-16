from beanie import Document
from enum import Enum
from pydantic import BaseModel, model_validator
from typing import List, Optional
from enum import Enum
from api.v1.routes.manga.models import Page, Volume

class TabCond(Enum):
    volumes = ["bunkoban", "saga"]
    chapters = ["arc", "duel", "characters"]
    pages = ["page_filters"]

class FilterQueries(BaseModel):
    bunkoban:       bool                = False
    saga:           Optional[str]       = None
    arc:            Optional[List[str]] = None
    duel:           Optional[List[str]] = None
    characters:     Optional[List[str]] = None
    page_filters:   Optional[List[str]] = None

    class Settings:
        page_filters = [
            "volume_cover",
            "chapter_cover",
            "author_notes",
            "tarot",
            "extra_illust",
            "game"
        ]

    def filled_fields(self):
        return [field for field in self.model_dump().keys() if getattr(self, field) is not None]

    @model_validator(mode="after")
    def validate_tab(self, tab: str):

        # required fields for each tab
        tab_cond = dict(
            volumes = all(item in set(self.filled_fields()) for item in TabCond.volumes.value),
            chapters = any(item in TabCond.chapters.value for item in self.filled_fields()),
            pages = TabCond.pages.value in self.filled_fields()
        )

        for cond in tab_cond.keys():
            if cond == tab and not tab_cond[cond]:
                raise ValueError(f"{cond} fields required".capitalize())

        return self

    async def build_query(self, tab: str):
        filled_fields = self.filled_fields()
        

        query_dict = dict()
        # Volume.[field] or Page.volume.[field]
        vol_prefix = "" if tab is "volumes" else "volume."

        # filter the volume filters requested
        vol_fields = [x for x in TabCond.volumes.value if x in filled_fields]
        for vol_f in vol_fields:
            query_dict[f"{vol_prefix}{vol_f}"] = getattr(self, vol_f)

        if tab is "volumes":
            query = await Volume.find(query_dict)

        # Page is linked to Volume and Chapter, Chapter and Volume are not linked to each other
        # full fetched queries must be filtered through Page
        # all queries must include Volume.bunkoban
        else:
            query_dict = self.fetch_links_query(query_dict, tab is "pages")
            query = await Page.find(query_dict, fetch_links=True)

        if tab is "chapters":
            results = query.distinct("chapter")
        else:
            results = query.to_list()

        return results

    def fetch_links_query(self, query_dict: dict, pages: bool):
        filled_fields = self.filled_fields()
        # filter the chapter filters requested
        chap_fields = [x for x in TabCond.chapters.value if x in filled_fields]
        for chap_f in chap_fields:
            query_dict[f"chapter.{chap_f}"] = getattr(self, chap_f)

        if pages:
            # filter the page filters requested
            page_fields = [x for x in self.Settings.page_filters if x in self.page_filters]
            for page_f in page_fields:
                query_dict[f"{page_f}"] = True

        return query_dict


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