from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.uploads import save_upload
from app.database import get_db
from app.models.user import User
from app.routers.posts import get_post_or_404, to_response
from app.schemas.blog import PostResponse

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/{slug}/cover", response_model=PostResponse)
async def upload_cover(
    slug: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PostResponse:
    post = get_post_or_404(db, slug, user)
    if post.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    post.cover_image = await save_upload(file)
    db.commit()
    db.refresh(post)
    return to_response(post, db)
