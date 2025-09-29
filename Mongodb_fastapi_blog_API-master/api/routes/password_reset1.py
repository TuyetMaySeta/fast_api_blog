from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..schemas import PasswordReset, PasswordResetRequest
from ..database import get_db
from ..models import User
from ..send_email import password_reset
from ..oauth2 import create_access_token, get_current_user
from ..utils import get_password_hash

router = APIRouter(
    prefix="/password",
    tags=["Password Reset"]
)

@router.post("/request/")
async def reset_request(
    user_email: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == user_email.email))
    user = result.scalar_one_or_none()

    if user is not None:
        token = create_access_token({"id": user.id})
        reset_link = f"http://localhost:8000/reset?token={token}"

        try:
            await password_reset(
                "Password Reset",
                user.email,
                {
                    "title": "Password Reset",
                    "name": user.name,
                    "reset_link": reset_link
                }
            )
        except Exception as e:
            print(f"Email error: {e}")
        
        return {"msg": "Email has been sent with instructions to reset your password."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Your details not found, invalid email address"
        )

@router.put("/reset/")
async def reset(
    token: str,
    new_password: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    # Get current user from token
    current_user = await get_current_user(token, db)
    
    # Update password
    current_user.password = get_password_hash(new_password.password)
    
    await db.commit()
    await db.refresh(current_user)
    
    return {"msg": "Password updated successfully"}