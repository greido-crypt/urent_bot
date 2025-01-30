from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from web_app.configuration.server import Server


def create_app(_=None) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all _headers
    )
    return Server(app).get_app()