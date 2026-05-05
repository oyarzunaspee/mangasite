from pydantic import BaseModel, computed_field
from beanie import Document
from typing import List
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
    author: str | None
    year: int
    pages: List[BookPage]

    class Settings:
        name = "books"