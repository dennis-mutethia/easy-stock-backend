from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from utils.models import Shop_Types, Users
from utils.database import get_session
from routes.auth import get_current_user 

router = APIRouter(prefix="/shops", tags=["Shop Types"])

@router.get("/types", response_model=List[Shop_Types])
async def get_shop_Types(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Shop_Types))
    return result.scalars().all()

@router.get("/types/{shop_type_id}", response_model=Shop_Types)
async def get_shop_type(
    shop_type_id: int,
    session: AsyncSession = Depends(get_session)
):
    statement = select(Shop_Types).where(Shop_Types.id == shop_type_id)    
    result = await session.execute(statement)
    shop_type = result.scalar_one_or_none()

    if not shop_type:
        raise HTTPException(status_code=404, detail="Shop type not found")

    return shop_type

@router.post("/types", response_model=Shop_Types, status_code=201)
async def create_shop_type(
    shop_type: Shop_Types,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    if current_user.user_level.level != 0:
        raise HTTPException(status_code=403, detail="Only super-admin can create Shop_Types")
    
    shop_type.created_by = current_user.id
    session.add(shop_type)
    await session.commit()
    await session.refresh(shop_type)
    return shop_type

@router.patch("/types/{shop_type_id}", response_model=Shop_Types)
async def update_shop_type(
    shop_type_id: int,
    shop_type_update: Shop_Types,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Only super-admin (user_level_id == 0) can update Shop_Types
    if current_user.user_level_id != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin can update Shop_Types"
        )

    # Fetch the existing shop_type
    statement = select(Shop_Types).where(Shop_Types.id == shop_type_id)
    result = await session.execute(statement)
    db_shop_type = result.scalar_one_or_none()

    if not db_shop_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop type not found"
        )

    # Get the update data as dict (only fields that were sent)
    update_data = shop_type_update.model_dump(exclude_unset=True)
    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_shop_type, key, value)

    # Update audit fields
    db_shop_type.updated_by = current_user.id
    db_shop_type.updated_at = datetime.now()

    # Commit changes
    session.add(db_shop_type)
    await session.commit()
    await session.refresh(db_shop_type)

    return db_shop_type