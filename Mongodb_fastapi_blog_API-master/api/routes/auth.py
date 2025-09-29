from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..schemas import Token
from ..database import get_db
from ..models import User
from .. import utils
from .. import oauth2

router = APIRouter(
    prefix="/login",
    tags=["Authentication"]
)

@router.post("", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Find user by username
    result = await db.execute(select(User).where(User.name == user_credentials.username))
    user = result.scalar_one_or_none()

    if user and utils.verify_password(user_credentials.password, user.password):
        access_token = oauth2.create_access_token(payload={"id": user.id})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user credentials"
        )