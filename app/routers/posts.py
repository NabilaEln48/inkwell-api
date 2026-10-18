from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, get_optional_user
from app.core.slugify import unique_post_slug, unique_tag_slug
from app.database import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.tag import Tag
from app.models.user import User
from app.schemas.blog import PostCreate, PostResponse, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])


def get_or_create_tag(db: Session, name: str) -> Tag:
    cleaned = name.strip()
    tag = db.query(Tag).filter(func.lower(Tag.name) == cleaned.lower()).first()
    if tag is None:
        tag = Tag(name=cleaned, slug=unique_tag_slug(db, cleaned))
        db.add(tag)
        db.flush()
    return tag


def get_post_or_404(db: Session, slug: str, user: User | None) -> Post:
    post = (
        db.query(Post)
        .options(joinedload(Post.author), joinedload(Post.tags))
        .filter(Post.slug == slug)
        .first()
    )
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if not post.published and (user is None or user.id != post.author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


def to_response(post: Post, db: Session) -> PostResponse:
    comment_count = db.query(func.count(Comment.id)).filter(Comment.post_id == post.id).scalar()
    response = PostResponse.model_validate(post)
    response.comment_count = comment_count or 0
    if post.cover_image:
        response.cover_image_url = f"/uploads/{post.cover_image}"
    return response


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PostResponse:
    post = Post(
        title=payload.title,
        slug=unique_post_slug(db, payload.title),
        body=payload.body,
        author_id=user.id,
    )
    post.tags = [get_or_create_tag(db, name) for name in payload.tag_names]
    db.add(post)
    db.commit()
    db.refresh(post)
    return to_response(post, db)


@router.get("", response_model=list[PostResponse])
def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tag: str | None = None,
    author_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> list[PostResponse]:
    query = db.query(Post).options(joinedload(Post.author), joinedload(Post.tags))

    if user is None:
        query = query.filter(Post.published.is_(True))
    else:
        query = query.filter(
            or_(Post.published.is_(True), Post.author_id == user.id)
        )

    if tag is not None:
        query = query.join(Post.tags).filter(func.lower(Tag.slug) == tag.lower())

    if author_id is not None:
        query = query.filter(Post.author_id == author_id)

    if q is not None:
        pattern = f"%{q}%"
        query = query.filter(or_(Post.title.ilike(pattern), Post.body.ilike(pattern)))

    posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    return [to_response(post, db) for post in posts]


@router.get("/{slug}", response_model=PostResponse)
def get_post(
    slug: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> PostResponse:
    post = get_post_or_404(db, slug, user)
    return to_response(post, db)


@router.patch("/{slug}", response_model=PostResponse)
def update_post(
    slug: str,
    payload: PostUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PostResponse:
    post = get_post_or_404(db, slug, user)
    if post.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if payload.title is not None:
        post.title = payload.title
        post.slug = unique_post_slug(db, payload.title)
    if payload.body is not None:
        post.body = payload.body
    if payload.tag_names is not None:
        post.tags = [get_or_create_tag(db, name) for name in payload.tag_names]
    db.commit()
    db.refresh(post)
    return to_response(post, db)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    post = get_post_or_404(db, slug, user)
    if post.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    db.delete(post)
    db.commit()


@router.post("/{slug}/publish", response_model=PostResponse)
def publish_post(
    slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PostResponse:
    post = get_post_or_404(db, slug, user)
    if post.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    post.published = True
    db.commit()
    db.refresh(post)
    return to_response(post, db)


@router.post("/{slug}/unpublish", response_model=PostResponse)
def unpublish_post(
    slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PostResponse:
    post = get_post_or_404(db, slug, user)
    if post.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    post.published = False
    db.commit()
    db.refresh(post)
    return to_response(post, db)
