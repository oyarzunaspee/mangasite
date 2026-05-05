from fastapi import APIRouter, status, Cookie
from .models import Book
from api.v1.routes.auth.decorators import auth_user
from fastapi_problem.error import ServerProblem


router = APIRouter(prefix="/books", tags=["books"])

# list of books
@router.get("")
@auth_user
async def get_books(
    token: str | None = Cookie(default=None)
):
    try:

        books = await Book.aggregate([{
            "$project": {
                "_id": {"$toString": "$_id"},
                "short": 1,
                "type": 1
            }
        }]).to_list()

        return {"status": status.HTTP_200_OK, "books": books}
    except Exception as e:
        raise ServerProblem(detail=e)

# book detail
@router.get("/{book_id}")
@auth_user
async def get_book(
    book_id: str,
    token: str | None = Cookie(default=None)
):
    try:

        book = await Book.get(book_id)

        return {"status": status.HTTP_200_OK, "book": book}
    except Exception as e:
        raise ServerProblem(detail=e)