from fastapi import APIRouter
from .auth.routes import router as auth_router
from .manga.routes import router as manga_router
from .books.routes import router as book_router
from .filter.routes import router as filter_router

router = APIRouter(prefix="/v1")
router.include_router(auth_router)
router.include_router(manga_router)
router.include_router(book_router)
router.include_router(filter_router)