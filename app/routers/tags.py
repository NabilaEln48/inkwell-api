from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.post import Post
from app.models.tag import Tag, post_tags
from app.schemas.blog import TagResponse

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def list_tags(db: Session = Depends(get_db)) -> list[TagResponse]:
    tags = db.query(Tag).order_by(Tag.name.asc()).all()
    return [TagResponse.model_validate(tag) for tag in tags]


@router.get("/popular", response_model=list[dict])
def popular_tags(db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(Tag, func.count(post_tags.c.post_id).label("post_count"))
        .join(post_tags, post_tags.c.tag_id == Tag.id)
        .join(Post, Post.id == post_tags.c.post_id)
        .filter(Post.published.is_(True))
        .group_by(Tag.id)
        .order_by(func.count(post_tags.c.post_id).desc())
        .limit(10)
        .all()
    )
    return [
        {"id": tag.id, "name": tag.name, "slug": tag.slug, "post_count": count}
        for tag, count in rows
    ]
