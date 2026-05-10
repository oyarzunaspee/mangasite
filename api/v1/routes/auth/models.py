from beanie import Document
from pydantic import BaseModel
from typing import List
import jwt
from datetime import timezone, datetime, timedelta
import os
from dotenv import load_dotenv
from beanie.odm.operators.update.array import AddToSet

load_dotenv()

class Token(BaseModel):
    user_agent: str
    encode: str


class AllowedUser(Document):
    username: str
    active: bool
    tokens: List[Token]

    class Settings:
        name = "allowed_users"

    @classmethod
    async def get_user(cls, username: str):
        return await AllowedUser.find(AllowedUser.username == username, AllowedUser.active == True).first_or_none()
    
    @classmethod
    async def set_token(cls, username: str):
        token = cls.create_access_token(username)
        return token

    @classmethod
    def create_access_token(cls, username: str):
        encoded_jwt = jwt.encode(
            {
                "sub": username, 
                "exp": datetime.now(tz=timezone.utc) + timedelta(days=int(os.getenv("ACCESS_TOKEN_EXPIRE")))
            }, 
            os.getenv("JWT_SECRET"), 
            algorithm=os.getenv("JWT_ALGO"))
  
        return encoded_jwt

    @classmethod    
    def get_token_user(cls, access_token: str):
        payload = jwt.decode(access_token, os.getenv("JWT_SECRET"), algorithms=[os.getenv("JWT_ALGO")])
        
        username = payload.get("sub")
        return username
    
    @classmethod
    async def authorize_user(cls, access_token: str):
        username = cls.get_token_user(access_token)
        allowed_user = await AllowedUser.get_user(username)
        return True if allowed_user else False