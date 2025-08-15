from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from .settings import settings

def setup_cors(app: FastAPI) -> None:
    """Configura CORS para la aplicación FastAPI"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
