from fastapi import Request
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import os

load_dotenv()

REDIRECT_URL = os.getenv("REDIRECT_URL")


async def custom_404_handler(request: Request, exc: Exception):
    return RedirectResponse(REDIRECT_URL)