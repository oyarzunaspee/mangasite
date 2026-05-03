from fastapi import APIRouter, HTTPException, status
from .models import Book


router = APIRouter(prefix="/books", tags=["books"])

# list of books
@router.get("")
async def get_books():
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
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {e}")

# book detail
@router.get("/{book_id}")
async def get_book(book_id: str):
    try:

        book = await Book.get(book_id)

        return {"status": status.HTTP_200_OK, "book": book}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {e}")