from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import traceback
import sys

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
    print("\n" + "="*60, file=sys.stderr)
    print("🔵 REGISTRATION REQUEST RECEIVED", file=sys.stderr)
    print(f"Name: {user_info.name}", file=sys.stderr)
    print(f"Email: {user_info.email}", file=sys.stderr)
    print(f"Password length: {len(user_info.password)}", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    try:
        # Check username
        print("📝 Step 1: Checking username...", file=sys.stderr)
        result = await db.execute(select(UserModel).where(UserModel.name == user_info.name))
        username_found = result.scalar_one_or_none()
        
        if username_found:
            print(f"❌ Username '{user_info.name}' already exists!", file=sys.stderr)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="There already is a user by that name"
            )
        print("✅ Username available", file=sys.stderr)

        # Check email
        print("📝 Step 2: Checking email...", file=sys.stderr)
        result = await db.execute(select(UserModel).where(UserModel.email == user_info.email))
        email_found = result.scalar_one_or_none()
        
        if email_found:
            print(f"❌ Email '{user_info.email}' already exists!", file=sys.stderr)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="There already is a user by that email"
            )
        print("✅ Email available", file=sys.stderr)

        # Hash password
        print("📝 Step 3: Hashing password...", file=sys.stderr)
        try:
            hashed_password = get_password_hash(user_info.password)
            print(f"✅ Password hashed (length: {len(hashed_password)})", file=sys.stderr)
        except Exception as e:
            print(f"❌ PASSWORD HASH FAILED: {e}", file=sys.stderr)
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password hashing failed: {str(e)}"
            )

        # Create user
        print("📝 Step 4: Creating user object...", file=sys.stderr)
        new_user = UserModel(
            name=user_info.name,
            email=user_info.email,
            password=hashed_password,
            api_key=secrets.token_hex(20)
        )
        print("✅ User object created", file=sys.stderr)
        
        # Save to DB
        print("📝 Step 5: Saving to database...", file=sys.stderr)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        print(f"✅ User saved with ID: {new_user.id}", file=sys.stderr)

        # Send email
        print("📝 Step 6: Sending email...", file=sys.stderr)
        try:
            await send_registration_mail(
                "Registration successful",
                new_user.email,
                {
                    "title": "Registration successful",
                    "name": new_user.name
                }
            )
            print("✅ Email sent successfully", file=sys.stderr)
        except Exception as email_error:
            print(f"⚠️ Email failed (ignored): {email_error}", file=sys.stderr)

        print("="*60, file=sys.stderr)
        print("🎉 REGISTRATION COMPLETED SUCCESSFULLY", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
        
        return new_user
        
    except HTTPException as he:
        print(f"⚠️ HTTP Exception: {he.detail}", file=sys.stderr)
        raise
    except Exception as e:
        print("="*60, file=sys.stderr)
        print(f"💥 UNEXPECTED ERROR: {type(e).__name__}", file=sys.stderr)
        print(f"Message: {str(e)}", file=sys.stderr)
        print("="*60, file=sys.stderr)
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/details", response_model=UserResponse)
async def details(current_user: UserModel = Depends(oauth2.get_current_user)):
    return current_user