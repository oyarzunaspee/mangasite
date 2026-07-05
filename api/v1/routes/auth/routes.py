from fastapi import APIRouter, Request, status, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
import os
from .models import AllowedUser
from fastapi_problem.error import ServerProblem, UnauthorisedProblem


load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()

oauth.register(
    name="twitter",
    client_id=os.getenv("TWITTER_CLIENT_ID"),
    client_secret=os.getenv("TWITTER_CLIENT_SECRET"),
    authorize_url="https://twitter.com/i/oauth2/authorize",
    access_token_url="https://api.twitter.com/2/oauth2/token",
    client_kwargs={
        "scope": "tweet.read users.read",
        "code_challenge_method": "S256",
    },
)


@router.get("/twitter")
async def login(request: Request):
    return await oauth.twitter.authorize_redirect(
        request,
        os.getenv("TWITTER_CALLBACK_URL")
    )

@router.get("/twitter/callback")
async def callback(request: Request):
    try:
        token = await oauth.twitter.authorize_access_token(request)

        user = await oauth.twitter.get("https://api.twitter.com/2/users/me", token=token)

        user_data = user.json()["data"]

        user_allowed = await AllowedUser.get_user(user_data["username"])

        response = RedirectResponse(
            url=os.getenv("FRONTEND_URL")
        )

        if user_allowed:
            new_token = await AllowedUser.set_token(user_data["username"])

            response.set_cookie(
            key = "token",
            value = new_token,
            httponly=True,
            secure=True,
            samesite="none"
            )
            return response
    except Exception as e:
        raise ServerProblem(detail=str(e))

@router.post("/authorize")
async def authorize(request: Request):
    try:
        token = request.headers["cookie"]["token"]
        allowed_user = await AllowedUser.authorize_user(token)
        return {"status": status.HTTP_200_OK, "allowed": allowed_user}
    except KeyError:
        raise UnauthorisedProblem(detail="No token")
    except Exception as e:
        raise ServerProblem(detail=e)