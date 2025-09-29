from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import traceback

from ..schemas import User, UserResponse
from ..database import get_db
from ..models import User as UserModel
from ..utils import get_password_hash
from ..send_email import send_registration_mail
from .. import oauth2

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/registration", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def registration(user_info: User, db: AsyncSession = Depends(get_db)):
    try:
        # Check for duplications
        result = await db.execute(select(UserModel).where(UserModel.name == user_info.name))
        username_found = result.scalar_one_or_none()
        
        if username_found:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="There already is a user by that name"
            )

        result = await db.execute(select(UserModel).where(UserModel.email == user_info.email))
        email_found = result.scalar_one_or_none()
        
        if email_found:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="There already is a user by that email"
            )

        # Create new user
        new_user = UserModel(
            name=user_info.name,
            email=user_info.email,
            password=get_password_hash(user_info.password),
            api_key=secrets.token_hex(20)
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Send email - ignore errors
        try:
            await send_registration_mail(
                "Registration successful",
                new_user.email,
                {
                    "title": "Registration successful",
                    "name": new_user.name
                }
            )
        except Exception as email_error:
            print(f"⚠️ Email error (ignored): {email_error}")

        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {e}")
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/details", response_model=UserResponse)
async def details(current_user: UserModel = Depends(oauth2.get_current_user)):
    return current_user