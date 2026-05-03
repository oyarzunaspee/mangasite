from fastapi import FastAPI
import uvicorn
from connection import lifespan
from api.v1.routes import router
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi_problem.handler import add_exception_handler, new_exception_handler
import os
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(lifespan=lifespan)

exceptionHandler = new_exception_handler()
add_exception_handler(app, exceptionHandler)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"), same_site="none", https_only=True )


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", ssl_keyfile="path/to/key.pem", ssl_certfile="path/to/cert.pem")