# routes/licenses.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from utils.models import Companies, Shops, Users
from utils.database import get_session
from routes.auth import get_current_user

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("/")
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

@router.get("/{company_id}")
async def get_company(
    company_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Super-admin (level 0) sees ALL Companies
    if current_user.user_level_id == 0:
        statement = select(Companies).where(Companies.id == company_id)
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
    company = result.scalars().first()

    if not company:
        raise HTTPException(status_code=404, detail="No company found")

    return company

@router.post("/", response_model=Companies, status_code=201)
async def create_company(
    company: Companies, 
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):

    # Only super-admin & admin (user_level_id in 0, 1) can create Companies
    if current_user.user_level_id not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin & admin can create Companies"
        )
        
    session.add(company)
    try:
        await session.commit()
        await session.refresh(company)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="Company already exists") from ie
    return company

@router.patch("/{company_id}", response_model=Companies)
async def update_company(
    company_id: int,
    company_update: Companies,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):

    # Only super-admin & admin (user_level_id in 0, 1) can update Companies
    if current_user.user_level_id not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin & admin can update Companies"
        )

    # Fetch the existing company
    statement = select(Companies).where(Companies.id == company_id)
    result = await session.execute(statement)
    db_company = result.scalar_one_or_none()

    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Get the update data as dict (only fields that were sent)
    update_data = company_update.model_dump(exclude_unset=True)

    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_company, key, value)

    # Update audit fields
    db_company.updated_at = datetime.now()
    db_company.updated_by = current_user.id
    # Commit changes
    session.add(db_company)
    await session.commit()
    await session.refresh(db_company)

    return db_company