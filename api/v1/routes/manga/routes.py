from fastapi import APIRouter, status, Cookie
from .models import Page, IndividualPages, Chapter
from beanie.operators import Or
from api.v1.routes.auth.decorators import auth_user
from fastapi_problem.error import ServerProblem


router = APIRouter(prefix="/manga", tags=["manga"])


# volumes by bunkoban, saga
@router.get("")
@auth_user
async def get_volumes(
    bunkoban: bool = False,
    token: str | None = Cookie(default=None)
):
    try:
        volumes = await Page.query_volumes(bunkoban)

        return {"status": status.HTTP_200_OK, "volumes": volumes}
    except Exception as e:
        raise ServerProblem(detail=e)

# pages by chapter
@router.get("/{chap_num}/pages")
@auth_user
async def get_pages(
    chap_num: int,
    bunkoban: bool = False,
    token: str | None = Cookie(default=None)
):
    try:
        pages = await Page.find(
            Page.volume.bunkoban == bunkoban,
            Page.chapter.number == chap_num,
            fetch_links=True
        ).sort(+Page.number).project(IndividualPages).to_list()

        next_limit = await Chapter.find().sort(-Chapter.number).first_or_none()

        return {"status": status.HTTP_200_OK, "pages": pages, "next_limit": next_limit.number}
    except Exception as e:
        raise ServerProblem(detail=e)


# individual bunkoban comparison
@router.get("/{chap_num}/compare")
@auth_user
async def compare_bunkoban(
    chap_num: int, 
    bunkoban: bool = False,
    token: str | None = Cookie(default=None)
):
    try:
        pages = await Page.find(
            Page.chapter.number == chap_num, 
            Page.volume.bunkoban == (not bunkoban),
            Or(
                Page.content == True,
                Page.chapter_cover == True
            ),
            fetch_links=True
        ).sort(+Page.number).project(IndividualPages).to_list()

        request_pages = Page.find(
            Page.volume.bunkoban == bunkoban,
            Page.chapter.number == chap_num,
            Or(
                Page.chapter_cover == True,
                Page.content == True
            ),
            fetch_links=True
        )
        
        start = await request_pages.sort(+Page.number).first_or_none()
        end = await request_pages.sort(-Page.number).first_or_none()


        return {"status": status.HTTP_200_OK, "pages": pages, "page_range": [start.number, end.number]}
    except Exception as e:
        raise ServerProblem(detail=e)