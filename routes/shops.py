# routes/licenses.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from utils.models import Companies, Shops, Users
from utils.database import get_session
from routes.auth import get_current_user

router = APIRouter(prefix="/shops", tags=["Shops"])

@router.get("/")
async def get_shops(
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Super-admin (level 0) sees ALL Shops
    if current_user.user_level_id == 0:
        statement = select(Shops)
    # Admin user (level 1) & Supervisor (level 2) sees shops of their company
    elif current_user.user_level_id in [1, 2]:
        statement = (
            select(Shops)
            .join(Shops, Shops.company_id == Shops.company_id)
            .where(Users.id == current_user.id)
        )
    else:
        # Normal user: only see the shop they are attached to
        statement = (
            select(Shops)
            .join(Users, Users.shop_id == Shops.id)
            .where(Users.id == current_user.id)
        )

    result = await session.execute(statement)
    shops = result.scalars().all()

    if not shops:
        raise HTTPException(status_code=404, detail="No shop found")

    return shops

@router.get("/{shop_id}")
async def get_shop(
    shop_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Super-admin (level 0) sees ALL Shops
    if current_user.user_level_id == 0:
        statement = select(Shops).where(Shops.id == shop_id)
        
    # Admin user (level 1) & Supervisor (level 2) sees shops of their company
    elif current_user.user_level_id in [1, 2]:
        statement = (
            select(Shops)
            .join(Shops, Shops.company_id == Shops.company_id)
            .where(Shops.id == shop_id)
        )
    else:
        # Normal user: only see the shop they are attached to
        statement = (
            select(Shops)
            .where(Shops.id == shop_id)
            .where(Users.shop_id == shop_id)
        )

    result = await session.execute(statement)
    shop = result.scalars().first()

    if not shop:
        raise HTTPException(status_code=404, detail="No shop found")

    return shop

@router.post("/", response_model=Shops, status_code=201)
async def create_shop(
    shop: Shops, 
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    

    # Only super-admin & admin (user_level_id in 0, 1) can create shops
    if current_user.user_level_id not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin & admin can create shops"
        )

    session.add(shop)
    try:
        await session.commit()
        await session.refresh(shop)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="Shop already exists") from ie
    return shop


@router.patch("/{shop_id}", response_model=Shops)
async def update_shop(
    shop_id: int,
    shop_update: Shops,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):

    # Only super-admin & admin (user_level_id in 0, 1) can update shopa
    if current_user.user_level_id not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin & admin can update Shops"
        )

    # Fetch the existing shop
    statement = select(Shops).where(Shops.id == shop_id)
    result = await session.execute(statement)
    db_shop = result.scalar_one_or_none()

    if not db_shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found"
        )

    # Get the update data as dict (only fields that were sent)
    update_data = shop_update.model_dump(exclude_unset=True)

    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_shop, key, value)

    # Update audit fields
    db_shop.updated_at = datetime.now()
    db_shop.updated_by = current_user.id
    # Commit changes
    session.add(db_shop)
    await session.commit()
    await session.refresh(db_shop)

    return db_shop