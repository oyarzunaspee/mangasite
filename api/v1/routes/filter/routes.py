from fastapi import APIRouter, status, Cookie
from api.v1.routes.auth.decorators import auth_user
from api.v1.routes.manga.models import Page, Volume, Chapter
from .models import Character
from fastapi_problem.error import ServerProblem, BadRequestProblem
from beanie.operators import Or, In
from operator import itemgetter

router = APIRouter(prefix="/filter", tags=["filter"])


@router.get("")
@auth_user
async def filter_populate(
    token: str | None = Cookie(default=None)
    ):
    try:
        sagas = await Volume.distinct( "saga" , { "saga" : { "$ne" : None } } )
        arcs = await Chapter.distinct("arc", { "arc" : { "$ne" : None } })
        duels = await Chapter.distinct("duel", { "duel" : { "$ne" : None } })
        chars = await Character.find().to_list()

        return {
            "status": status.HTTP_200_OK,
            "filters": {
                "saga": sagas,
                "arc": sorted(arcs, key=itemgetter('number')),
                "duel": duels,
                "characters": chars
            }
        }
    except Exception as e:
        raise ServerProblem(detail=e)

@router.get("/volumes")
@auth_user
async def filter_chapters(
    saga: str = None,
    token: str | None = Cookie(default=None)
    ):
    try:
        volumes = await Page.query_volumes(saga=saga)
        return {"status": status.HTTP_200_OK, "volumes": volumes}
    except Exception as e:
        raise ServerProblem(detail=e)

@router.get("/chapters")
@auth_user
async def filter_chapters(
    arc: str = None,
    characters: str = None,
    duel: str = None,
    token: str | None = Cookie(default=None)
    ):
    try:
        if characters:
            characters = characters.split(",")
        chapters = await Chapter.find(
            Or(
            Chapter.arc == arc,
            In(Chapter.characters, characters),
            Chapter.duel == duel
            )
        ).sort(+Chapter.number).to_list()

        return {"status": status.HTTP_200_OK, "chapters": chapters}
    except Exception as e:
        raise ServerProblem(detail=e)

@router.get("/pages")
@auth_user
async def filter_pages(
    field: str,
    token: str | None = Cookie(default=None)
    ):
    try:
        if field not in list(Page.model_dump().keys()):
            raise BadRequestProblem(detail="Wrong field")
        match = {
            f"{field}": True
        }
        pages = await Page.find(match).to_list()

        return {"status": status.HTTP_200_OK, "pages": pages}
    except Exception as e:
        raise ServerProblem(detail=e)