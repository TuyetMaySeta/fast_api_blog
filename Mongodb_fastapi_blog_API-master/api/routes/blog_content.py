from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from typing import List

from ..schemas import BlogContent, BlogContentResponse
from ..database import get_db
from ..models import User, BlogPost
from .. import oauth2

router = APIRouter(
    prefix="/blog",
    tags=["Blog Content"]
)

@router.post("/", response_model=BlogContentResponse)
async def create_blog_post(
    blog_content: BlogContent,
    current_user: User = Depends(oauth2.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        new_post = BlogPost(
            title=blog_content.title,
            body=blog_content.body,
            author_id=current_user.id,
            author_name=current_user.name,
            created_at=datetime.utcnow()
        )
        
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)
        
        return new_post
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[BlogContentResponse])
async def get_blog_posts(
    limit: int = 4,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(BlogPost).order_by(desc(BlogPost.created_at)).limit(limit)
        )
        blog_posts = result.scalars().all()
        return blog_posts
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{id}", response_model=BlogContentResponse)
async def get_blog_post(id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(BlogPost).where(BlogPost.id == id))
        blog_post = result.scalar_one_or_none()
        
        if not blog_post:
            raise HTTPException(status_code=404, detail=f"Blog Post {id} not found")
        
        return blog_post
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{id}", response_model=BlogContentResponse)
async def update_blog_post(
    id: int,
    blog_content: BlogContent,
    current_user: User = Depends(oauth2.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == id))
    blog_post = result.scalar_one_or_none()
    
    if not blog_post:
        raise HTTPException(status_code=404, detail=f"Blog Post {id} not found")
    
    if blog_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this blog post")
    
    try:
        blog_post.title = blog_content.title
        blog_post.body = blog_content.body
        
        await db.commit()
        await db.refresh(blog_post)
        
        return blog_post
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog_post(
    id: int,
    current_user: User = Depends(oauth2.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == id))
    blog_post = result.scalar_one_or_none()
    
    if not blog_post:
        raise HTTPException(status_code=404, detail=f"Blog Post {id} not found")
    
    if blog_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this blog post")
    
    try:
        await db.delete(blog_post)
        await db.commit()
        return None
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")