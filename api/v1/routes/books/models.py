from pydantic import BaseModel, computed_field
from beanie import Document
from typing import List, Optional
from enum import Enum
from dotenv import load_dotenv
import os

load_dotenv()

URL = os.getenv('STORE_URL')


class BookType(str, Enum):
    art = "artbook"
    guide = "guidebook"

class BookPage(BaseModel):
    number: int
    link: str

    @computed_field
    @property
    def full_link(self) -> str:
        return f"{URL}{self.link}"


class Book(Document):
    type: BookType
    title: str
    short: str
    jpn: str
    publisher: str
    author: Optioal[str] = None
    year: int
    pages: List[BookPage]

    class Settings:
        name = "books"

    @classmethod
    async def get_books(cls):
        books = await cls.aggregate([{
            "$project": {
                "_id": {"$toString": "$_id"},
                "short": 1,
                "title": 1,
                "type": 1,
                "cover": {
                    "$concat": [
                        URL,
                        { "$arrayElemAt": ["$pages.link", 0] }
                    ]
                }
            }
        }]).to_list()
        return books