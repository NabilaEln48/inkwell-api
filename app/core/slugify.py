import re

from sqlalchemy.orm import Session

from app.models.post import Post

_slug_re = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    slug = _slug_re.sub("-", text.lower()).strip("-")
    return slug or "post"


def unique_post_slug(db: Session, title: str) -> str:
    base = slugify(title)
    slug = base
    counter = 2
    while db.query(Post).filter(Post.slug == slug).first() is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def unique_tag_slug(db: Session, name: str) -> str:
    from app.models.tag import Tag

    base = slugify(name)
    slug = base
    counter = 2
    while db.query(Tag).filter(Tag.slug == slug).first() is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug
