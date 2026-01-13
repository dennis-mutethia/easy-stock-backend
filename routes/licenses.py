# routes/licenses.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from typing import List

from models import Companies, Licenses, Shops, Users
from database import get_session
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