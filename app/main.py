from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, comments, posts, tags, uploads

import os

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="inkwell-api",
    description="Blog REST API — project 3 of a 15-project backend series.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(tags.router)
app.include_router(uploads.router)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/health", tags=["ops"])
def healthcheck() -> dict:
    return {"status": "ok"}
