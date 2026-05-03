from fastapi import APIRouter, HTTPException, status, Cookie

from beanie.operators import Or

router = APIRouter(prefix="/filter", tags=["filter"])