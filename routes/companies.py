# routes/licenses.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from models import Companies, Shops, Users
from database import get_session
from routes.auth import get_current_user

router = APIRouter(prefix="/licenses", tags=["Companies"])

@router.get("/companies")
async def get_companies(
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Super-admin (level 0) sees ALL Companies
    if current_user.user_level_id == 0:
        statement = select(Companies)
    else:
        # Normal user: only see license of their company
        # Join: User → Shop → Company → License
        statement = (
            select(Companies)
            .join(Shops, Shops.company_id == Companies.id)
            .join(Users, Users.shop_id == Shops.id)
            .where(Users.id == current_user.id)
        )

    result = await session.execute(statement)
    companies = result.scalars().all()

    if not companies and current_user.user_level.level != 0:
        raise HTTPException(status_code=404, detail="No company found")

    return companies

@router.post("/companies", response_model=Companies, status_code=201)
async def create_company(
    company: Companies, 
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    session.add(company)
    try:
        await session.commit()
        await session.refresh(company)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="Company already exists") from ie
    return company

