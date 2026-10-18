import sys

sys.path.insert(0, ".")

from app.core.security import hash_password
from app.core.slugify import unique_post_slug, unique_tag_slug
from app.database import Base, SessionLocal, engine
from app.models.comment import Comment
from app.models.post import Post
from app.models.tag import Tag
from app.models.user import User


def get_or_create_tag(db, name):
    tag = db.query(Tag).filter(Tag.name == name).first()
    if tag is None:
        tag = Tag(name=name, slug=unique_tag_slug(db, name))
        db.add(tag)
        db.flush()
    return tag


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    alice = User(email="alice@example.com", hashed_password=hash_password("secret123"))
    bob = User(email="bob@example.com", hashed_password=hash_password("secret123"))
    db.add_all([alice, bob])
    db.flush()

    posts_data = [
        (
            "Getting Started with FastAPI",
            "FastAPI is a modern Python web framework...",
            ["python", "fastapi"],
            True,
            alice,
        ),
        (
            "Understanding JWT Authentication",
            "JSON Web Tokens let you build stateless auth...",
            ["security", "python"],
            True,
            alice,
        ),
        (
            "Draft: My Secret Project",
            "Not ready for the world yet.",
            ["drafts"],
            False,
            bob,
        ),
    ]

    for title, body, tag_names, published, author in posts_data:
        post = Post(
            title=title,
            slug=unique_post_slug(db, title),
            body=body,
            published=published,
            author_id=author.id,
        )
        post.tags = [get_or_create_tag(db, name) for name in tag_names]
        db.add(post)
        db.flush()

    first = db.query(Post).filter(Post.slug == "getting-started-with-fastapi").first()
    db.add(Comment(body="Great introduction!", post_id=first.id, author_id=bob.id))
    db.add(Comment(body="Thanks for reading.", post_id=first.id, author_id=alice.id))

    db.commit()
    db.close()
    print("Seeded 2 users, 3 posts, 4 tags, 2 comments.")


if __name__ == "__main__":
    main()
