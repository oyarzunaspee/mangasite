from fastapi import APIRouter, status, Cookie, Query
from api.v1.routes.auth.decorators import auth_user
from api.v1.routes.manga.models import Page, Volume, Chapter
from api.v1.routes.manga.pipeline import PipelineDoc
from .models import Character, FilterQueries
from fastapi_problem.error import ServerProblem, BadRequestProblem
from beanie.operators import Or, In
from operator import itemgetter
from typing import Annotated, Optional
from enum import Enum
import pprint

class TabEnum(str, Enum):
    volumes = "volumes"
    chapters = "chapters"
    pages = "pages"

router = APIRouter(prefix="/filter", tags=["filter"])

@router.get("/{tab}")
async def perform_filter(
    tab: TabEnum,
    queries: Annotated[FilterQueries, Query()]
    ):
    try:
        # check conditional fields for each tab
        queries.validate_tab(tab.value)

        results = await queries.execute_query(tab.value)
        return {"status": status.HTTP_200_OK, "results": results}
    except Exception as e:
        raise ServerProblem(detail=e)


@router.get("")
@auth_user
async def filter_populate(
    token: Optional[str] = Cookie(default=None)
    ):
    try:
        exclude_none = { "$ne" : None }
        sagas = await Volume.distinct( "saga" , { "saga" : exclude_none } )
        arcs = await Chapter.distinct("arc", { "arc" : exclude_none })
        duels = await Chapter.distinct("duel", { "duel" : exclude_none })
        grouped_chars = await Character.get_groups()

        return {
            "status": status.HTTP_200_OK,
            "filters": {
                "saga": sagas,
                "arc": sorted(arcs, key=itemgetter("number")),
                "duel": duels,
                "groups": grouped_chars,
                "page": Page.Settings.page_filters
            }
        }
    except Exception as e:
        raise ServerProblem(detail=e)