from functools import wraps
from fastapi import HTTPException, status
from .models import AllowedUser
from fastapi_problem.error import UnauthorisedProblem
from jwt.exceptions import ExpiredSignatureError

def auth_user(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        token = kwargs["token"]
        print(kwargs)

        if not token:
            raise UnauthorisedProblem(detail="No token")

        try:
            user_allowed = await AllowedUser.authorize_user(token)
        except ExpiredSignatureError:
            raise UnauthorisedProblem(detail="Expired token")
        except Exception as e:
            raise UnauthorisedProblem(detail=e)

        return await func(*args, **kwargs)
    return wrapper