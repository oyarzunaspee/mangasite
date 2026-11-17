from beanie import Document
from enum import Enum
from pydantic import BaseModel, model_validator
from typing import List, Optional
from enum import Enum
from api.v1.routes.manga.models import Page, Volume
from api.v1.utils.custom_beanie import CustomDocument


class TabCond(Enum):
    volumes     = ["bunkoban", "saga"]
    chapters    = ["arc", "duel", "characters"]
    pages =     ["page_filter"]

class PageFilters(Enum):
    vol_cover   = "volume_cover"
    chap_cover  = "chapter_cover"
    author      = "author_notes"
    tarot       = "tarot"
    illust      = "extra_illust"
    game        = "game"

class FilterQueries(BaseModel):
    bunkoban:       bool                    = False
    saga:           Optional[str]           = None
    arc:            Optional[List[int]]     = None
    duel:           Optional[List[str]]     = None
    characters:     Optional[List[str]]     = None
    page_filter:    Optional[PageFilters]   = None

    class QueryConfig:
        # not just Document.[field] but Document.[field].[nested_field]
        nested_fields = [{
            "name": "arc",
            "nested_field": "number"
        }]
        all_operator = {"characters"} # as opposed to $in

    def provided_filters(self):
        return [field for field in type(self).model_fields if getattr(self, field) is not None]

    @model_validator(mode="after")
    def validate_tab(self, tab: str):
        provided_filters = self.provided_filters()

        # required fields for each tab
        tab_cond = dict(
            volumes = all(item in set(provided_filters) for item in TabCond.volumes.value),
            chapters = any(item in TabCond.chapters.value for item in provided_filters),
            pages = self.page_filter in [x.value for x in PageFilters]
        )

        for cond in tab_cond.keys():
            if cond == tab and not tab_cond[cond]:
                raise ValueError(f"{cond} fields required".capitalize())

        return self

    def fetch_links_query(self, query_dict: dict, pages_tab: bool, provided_filters: list):
        
        # QueryConfigct filled chapter filters
        chapter_fields = [x for x in TabCond.chapters.value if x in provided_filters]
    
        for chapter_f in chapter_fields:
            nested_fields = self.QueryConfig.nested_fields

            nested_query = next((f".{item["nested_field"]}" for item in nested_fields if item["name"] == chapter_f), "")
            operator = "all" if chapter_f in self.QueryConfig.all_operator else "in"

            chapter_query = f"chapter.{chapter_f}{nested_query}"
    
            query_dict[chapter_query] = {
                f"${operator}": getattr(self, chapter_f)
            }
                
        if pages_tab:
            query_dict[f"{self.page_filter}"] = True
    
        return query_dict

    async def execute_query(self, tab: str):     
        provided_filters = self.provided_filters() 

        query_dict = dict()
        # Volume.[field] or Page.volume.[field]
        volume_prefix = "" if tab == "volumes" else "volume."

        # extract filled volume filters
        volume_fields = [x for x in TabCond.volumes.value if x in provided_filters]
        for volume_f in volume_fields:
            query_dict[f"{volume_prefix}{volume_f}"] = getattr(self, volume_f)

        if tab == "volumes":
            query = Volume.find(query_dict).sort("number")

        else:
            # Page is linked to Volume and Chapter, Chapter and Volume are not linked to each other
            # full fetched queries must be filtered through Page
            # all queries must include Volume.bunkoban
            query_dict = self.fetch_links_query(
                query_dict, 
                tab == "pages",
                provided_filters
            )
            query = Page.find(query_dict, fetch_links=True)

        if tab == "chapters":
            results = await query.distinct("chapter")
        else:
            results = await query.to_list()

        return results


class Group(Enum):
    yugitachi =     (1, "Yugi & Friends")
    kc =            (2, "Kaiba Corp")
    ishtar =        (3, "Ishtar Family")
    antagonist =    (4, "Other Antagonists")
    duelist =       (5, "Duelists")
    memory =        (6, "Memory World")

class Character(CustomDocument):
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