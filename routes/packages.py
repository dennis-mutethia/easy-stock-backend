
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models import Packages, Users
from database import get_session
from routes.auth import get_current_user 

router = APIRouter(prefix="/packages", tags=["Packages"])

@router.get("/", response_model=List[Packages])
async def get_packages(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Packages))
    return result.scalars().all()

@router.post("/", response_model=Packages, status_code=201)
async def create_package(
    package: Packages,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    if current_user.user_level.level != 0:
        raise HTTPException(status_code=403, detail="Only super-admin can create packages")
    
    package.created_by = current_user.id
    session.add(package)
    await session.commit()
    await session.refresh(package)
    return package

@router.patch("/{package_id}", response_model=Packages)
async def update_package(
    package_id: int,
    package_update: Packages,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Only super-admin (user_level_id == 0) can update packages
    if current_user.user_level_id != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin can update packages"
        )

    # Fetch the existing package
    statement = select(Packages).where(Packages.id == package_id)
    result = await session.execute(statement)
    db_package = result.scalar_one_or_none()

    if not db_package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )

    # Get the update data as dict (only fields that were sent)
    update_data = package_update.model_dump(exclude_unset=True)

    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_package, key, value)

    # Update audit fields
    db_package.updated_at = datetime.now()
    db_package.updated_by = current_user.id

    # Commit changes
    session.add(db_package)
    await session.commit()
    await session.refresh(db_package)

    return db_package