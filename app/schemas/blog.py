from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserResponse


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class PostCreate(BaseModel):
    title: str
    body: str
    tag_names: list[str] = []


class PostUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    tag_names: list[str] | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    body: str
    published: bool
    cover_image_url: str | None = None
    author: UserResponse
    tags: list[TagResponse] = []
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    body: str


class CommentUpdate(BaseModel):
    body: str


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    post_id: int
    author: UserResponse
    created_at: datetime
