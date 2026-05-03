from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from fastapi import FastAPI
from contextlib import asynccontextmanager
import certifi
from beanie import init_beanie
import os
from api.v1.routes.manga.models import Volume, Chapter, Page
from api.v1.routes.books.models import Book
from api.v1.routes.auth.models import AllowedUser

load_dotenv()

uri = os.getenv(os.getenv('INIT'))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_db_client(app)
    yield
    await shutdown_db_client(app)

async def startup_db_client(app):
    app.mongodb_client = AsyncMongoClient(uri, tlsCAFile=certifi.where(), uuidRepresentation="standard")
    await init_beanie(database=app.mongodb_client.manga, document_models=[Chapter, Page, Volume, Book, AllowedUser])
    print("MongoDB connected.")

async def shutdown_db_client(app):
    app.mongodb_client.close()
    print("Database disconnected.")