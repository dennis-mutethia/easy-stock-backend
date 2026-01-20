
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from utils.database import get_session
from utils.helper_auth import authenticate_user, create_access_token, get_current_user
from utils.models import Users

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def login(
    phone: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(phone, password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id, 
            "name": user.name, 
            "phone": user.phone, 
            "shop_id": user.shop_id, 
            "user_level_id": user.user_level_id
        }
    }

@router.get("/me")
async def me(current_user: Users = Depends(get_current_user)):
    return current_user