from typing import List
import os
from dotenv import load_dotenv
from fastapi_problem.error import UnprocessableProblem

load_dotenv()

URL = os.getenv("STORE_URL")

class VolumePipeline:
    def match_volumes(self):
        match = {
            "volume.bunkoban": self.bunkoban
        }

        if self.saga:
            match["volume.saga"] = self.saga
        
        self.pipeline.append(
            {
                "$match": match
            }
        )
    

    def group_volumes(self):
        self.pipeline.append(
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
            }
        )

    def add_cover_page(self):
        self.pipeline += [
            {
                "$set": {
                    "first_chapter": { "$first": "$chapters" }
                }
            },
            {
                "$lookup": {
                    "from": "pages",
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
            }
        ]

    def prepare_project(self):
        self.pipeline.append(
            {
                "$project": {
                    "_id": 0,
                    "counter": "$volume.number" if self.saga else "$volume.counter",
                    "title": "$volume.title",
                    "cover": self.link(),
                    "chapters": 1
                }
            }
        )


class ChapterPipeline:
    
    def match_chapters(self):
        and_matches = []
       
        if len(self.characters[0]) > 0:
            and_matches.append(
                {
                    "chapter.characters": {"$in": self.characters}
                }
            )
        
        if len(self.duel[0]) > 0:
            and_matches.append(
                {
                    "chapter.duel": { "$in": self.duel}                        
                }
            )
        
        if len(self.arc[0]) > 0:
            and_matches.append(
                {
                    "chapter.arc.name": { "$in": self.arc}
                }
            )

        self.pipeline.append(
            {
                "$match": {
                    "$and": and_matches
                }
            }
        )


    def group_chapters(self):

        self.pipeline.append(
            {
            "$group": {
                "_id": "$chapter._id",
                "title": {"$first": "$chapter.title"},
                "number": {"$first": "$chapter.number"},
                "jpn": {"$first": "$chapter.jpn"},
                "volume": {"$first": "$volume"}
            }
        }
        )

class PagePipeline:
    def match_pages(self):
        or_match = []
        for field in self.page_filters:
            or_match.append(
                {
                    f"{field.toLowerCase()}": True
                }
            )

        match = {
            "$or": or_match
        }

        self.pipeline.append(
            {
                "$match": match
            }
        )
    
    def link(self):
        return {
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
        }

class PipelineDoc(VolumePipeline, ChapterPipeline, PagePipeline):
    def __init__(
            self, 
            tab: str = None,
            bunkoban: bool = False, 
            saga: str | None = None, 
            arc: List[str] | None = None,
            duel: List[str] | None = None,
            characters: List[str] | None = None,
            page_filters: List[str] | None = None
        ):
        self.bunkoban = bunkoban
        self.saga = saga
        self.arc = arc
        self.duel = duel
        self.characters = characters
        self.page_filters = page_filters

        self.validate_queries(tab)

        self.tab = tab or "volumes"

        self.pipeline = []

    def validate_queries(self, tab: str):
        volume_cond = tab == "volumes" and not self.saga
        chapter_cond = tab == "chapters" and (not self.duel and not self.characters)
        page_cond = tab == "pages" and not self.page_filters

        if volume_cond or chapter_cond or page_cond:
            raise UnprocessableProblem(detail=f"{tab.capitalize()} queries missing")
        

    def build_pipeline(self):

        match self.tab:
            case "volumes":
                self.build_volumes()

            case "chapters":
                self.build_chapters()

            case "pages":
                self.build_pages()

        return self.pipeline
    
    def build_volumes(self):
        self.lookup("volume")
        self.match_volumes()
        self.lookup("chapter")
        self.group_chapters()
        self.sort("number")
        self.group_volumes()
        self.sort("volume.counter")
        self.add_cover_page()
        self.prepare_project()
    
    def build_chapters(self):
        if self.saga:
            self.lookup("volume")
            self.match_volumes()
        self.lookup("chapter")
        self.match_chapters()
        self.group_chapters()
        self.sort("number")
        if self.saga:
            self.prepare_project()
        else:
            self.pipeline.append(
                {
                    "$project": {
                        "_id": 0,
                        "title": "$title",
                        "number": "$number",
                        "jpn": "$jpn"
                    }
                }
            )
    
    def build_pages(self):
        self.match_pages()
        self.sort("number")
        self.lookup_volume()
        self.lookup_chapter()
        if self.arc or self.duel or self.characters: 
            self.match_chapters()

        self.pipeline.append(
            {
                "$project": {
                    "_id": 0,
                    "number": 1,
                    "double": 1,
                    "content": 1,
                    "link": self.link()
                }
            }
        )

    def lookup(self, field: str):
        self.pipeline += [
            {
                "$lookup": {
                    "from": f"{field}s",
                    "localField": f"{field}.$id",
                    "foreignField": "_id",
                    "as": f"{field}"
                }
            },
            {"$unwind": f"${field}"}
        ]
    
    def sort(self, field: str):
        self.pipeline.append(
            {
                "$sort": {f"{field}": 1}
            }
        )