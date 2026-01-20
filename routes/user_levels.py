from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from utils.models import User_Levels, Users
from utils.database import get_session
from routes.auth import get_current_user 

router = APIRouter(prefix="/users", tags=["User Levels"])

@router.get("/levels/", response_model=List[User_Levels])
async def get_user_levels(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User_Levels))
    return result.scalars().all()

@router.get("/levels/{user_level_id}", response_model=User_Levels)
async def get_user_level(
    user_level_id: int,
    session: AsyncSession = Depends(get_session)
):
    statement = select(User_Levels).where(User_Levels.id == user_level_id)    
    result = await session.execute(statement)
    user_level = result.scalar_one_or_none()

    if not user_level:
        raise HTTPException(status_code=404, detail="User Level not found")

    return user_level

@router.post("/levels/", response_model=User_Levels, status_code=201)
async def create_user_level(
    user_level: User_Levels,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    if current_user.user_level_id != 0:
        raise HTTPException(status_code=403, detail="Only super-admin can create user levels")

    user_level.created_by = current_user.id
    user_level.created_at = datetime.now()
    
    session.add(user_level)
    await session.commit()
    await session.refresh(user_level)
    return user_level

@router.patch("/levels/{user_level_id}", response_model=User_Levels)
async def update_user_level(
    user_level_id: int,
    user_level_update: User_Levels,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Only super-admin (user_level_id == 0) can update user levels
    if current_user.user_level_id != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin can update user levels"
        )

    # Fetch the existing user level
    statement = select(User_Levels).where(User_Levels.id == user_level_id)
    result = await session.execute(statement)
    db_user_level = result.scalar_one_or_none()

    if not db_user_level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Level not found"
        )

    # Get the update data as dict (only fields that were sent)
    update_data = user_level_update.model_dump(exclude_unset=True)

    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_user_level, key, value)

    # Update audit fields
    db_user_level.updated_by = current_user.id
    db_user_level.updated_at = datetime.now()
    # Commit changes
    session.add(db_user_level)
    await session.commit()
    await session.refresh(db_user_level)

    return db_user_level