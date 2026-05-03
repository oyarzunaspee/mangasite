from functools import wraps
from fastapi import HTTPException, status
from .models import AllowedUser
from fastapi_problem.error import UnauthorisedProblem

def auth_user(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        token = kwargs["token"]

        if not token:
            raise UnauthorisedProblem(detail="No token")

        try:
            user_allowed = await AllowedUser.authorize_user(token)
        except Exception as e:
            raise UnauthorisedProblem(detail=e)

        return await func(*args, **kwargs)
    return wrapper