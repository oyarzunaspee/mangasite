from beanie import Document
from pydantic import BaseModel
from typing import List
from joserfc import jwt
from joserfc.jwk import OctKey
from datetime import timedelta, UTC, datetime
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
    async def set_token(cls, username: str, user_agent: str):
        token = cls.create_access_token(username)
        user = await cls.get_user(username)
        if user:
            new_token = Token(
                user_agent=user_agent,
                encode=token
            )
            await user.update(AddToSet({cls.tokens: new_token}))
        return token

    @classmethod
    def create_access_token(cls, username: str):       
        now = datetime.datetime.now(datetime.UTC)
        claims = {
            "sub": username,
            "iat": now,
            "exp": now + timedelta(int(os.getenv("ACCESS_TOKEN_EXPIRE"))),
        }
        header = {"alg": os.getenv("JWT_SECRET")}
        key = os.getenv("JWT_SECRET")
        encoded_jwt = jwt.encode(header, claims, key)

        return encoded_jwt

    @classmethod    
    def get_token_user(cls, access_token: str):
        key = os.getenv("JWT_SECRET")

        payload = jwt.decode(access_token, key, algorithms=os.getenv("JWT_ALGO"))

        username = payload.get("sub")
        return username
    
    @classmethod
    async def authorize_user(cls, access_token: str):
        username = cls.get_token_user(access_token)
        allowed_user = await AllowedUser.get_user(username)
        return True if allowed_user else False