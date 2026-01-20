# routes/licenses.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from typing import List

from utils.models import Companies, Licenses, Shops, Users
from utils.database import get_session
from routes.auth import get_current_user

router = APIRouter(prefix="/licenses", tags=["Licenses"])

@router.get("/", response_model=List[Licenses])
async def get_licenses(
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Super-admin (level 0) sees ALL licenses
    if current_user.user_level_id == 0:
        statement = select(Licenses)
    else:
        # Normal user: only see license of their company
        # Join: User → Shop → Company → License
        statement = (
            select(Licenses)
            .join(Companies, Companies.license_id == Licenses.id)
            .join(Shops, Shops.company_id == Companies.id)
            .join(Users, Users.shop_id == Shops.id)
            .where(Users.id == current_user.id)
        )

    result = await session.execute(statement)
    licenses = result.scalars().all()

    if not licenses and current_user.user_level.level != 0:
        raise HTTPException(status_code=404, detail="No license found for your company")

    return licenses


@router.post("/", response_model=Licenses, status_code=201)
async def create_license(
    license: Licenses, 
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    session.add(license)
    try:
        await session.commit()
        await session.refresh(license)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="License already exists") from ie
    return license


@router.patch("/{license_id}", response_model=Licenses)
async def update_license(
    license_id: int,
    license_update: Licenses,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Only super-admin (user_level_id == 0) can update licenses
    if current_user.user_level_id != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin can update Licenses"
        )

    # Fetch the existing license
    statement = select(Licenses).where(Licenses.id == license_id)
    result = await session.execute(statement)
    db_license = result.scalar_one_or_none()

    if not db_license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )

    # Get the update data as dict (only fields that were sent)
    update_data = license_update.model_dump(exclude_unset=True)

    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_license, key, value)

    # Update audit fields
    db_license.updated_at = datetime.now()
    db_license.updated_by = current_user.id
    # Commit changes
    session.add(db_license)
    await session.commit()
    await session.refresh(db_license)

    return db_license