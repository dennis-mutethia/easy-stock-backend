from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from utils.models import Shops, Users
from utils.database import get_session
from routes.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
async def get_shops(
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Super-admin (level 0) sees ALL Users
    if current_user.user_level_id == 0:
        statement = select(Users)
    # Admin user (level 1) sees users of their company
    elif current_user.user_level_id in [1, 2]:
        user_shop_statement =(
            select(Shops)
            .join(Users, Users.shop_id == Shops.id)
            .where(Users.id == current_user.id)
        )
        shop_result = await session.execute(user_shop_statement)
        user_shop = shop_result.scalar_one_or_none()
        
        statement = (
            select(Users)
            .join(Shops, Users.shop_id == Shops.id)            
            .where(Shops.company_id == user_shop.company_id)
        )
        
    else:
        # Normal user: only see users in their own shop
        statement = (
            select(Users)
            .join(Shops, Users.shop_id == Shops.id)
            .where(Users.id == current_user.id)
        )

    result = await session.execute(statement)
    shops = result.scalars().all()

    if not shops:
        raise HTTPException(status_code=404, detail="No users found")

    return shops

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    # Super-admin (level 0) sees ALL Users
    if current_user.user_level_id == 0:
        statement = select(Users).where(Users.id == user_id)

    # Admin user (level 1) & Supervisor (level 2) sees users of their company
    elif current_user.user_level_id in [1, 2]:
        user_shop_statement =(
            select(Shops)
            .join(Users, Users.shop_id == Shops.id)
            .where(Users.id == current_user.id)
        )
        shop_result = await session.execute(user_shop_statement)
        user_shop = shop_result.scalar_one_or_none()

        statement = (
            select(Users)
            .join(Shops, Users.shop_id == Shops.id)
            .where(Shops.company_id == user_shop.company_id)
            .where(Users.id == user_id)
        )

    else:
        # Normal user: only see users in their own shop
        statement = (
            select(Users)
            .join(Shops, Users.shop_id == Shops.id)
            .where(Users.id == user_id)
            .where(Users.shop_id == current_user.shop_id)
        )

    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.post("/", response_model=Users, status_code=201)
async def create_user(
    user: Users, 
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    

    # Only super-admin & admin (user_level_id in 0, 1) can create shops
    if current_user.user_level_id not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin & admin can create shops"
        )

    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="User already exists") from ie
    return user


@router.patch("/{user_id}", response_model=Users)
async def update_user(
    user_id: int,
    user_update: Users,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):

    # Only super-admin & admin (user_level_id in 0, 1) can update shopa
    if current_user.user_level_id not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin & admin can update Users"
        )

    # Fetch the existing user
    statement = select(Users).where(Users.id == user_id)
    result = await session.execute(statement)
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    
    #if admin level is 1, restrict to only update own company users
    if current_user.user_level_id == 1:
        # Verify that the shop belongs to the user's company
        user_shop_statement =(
            select(Shops)
            .join(Users, Users.shop_id == Shops.id)
            .where(Shops.company_id == db_user.shop.company_id)
            .where(Users.id == current_user.id)
        )
        shop_result = await session.execute(user_shop_statement)
        user_shop = shop_result.scalar_one_or_none()
        if not user_shop:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin can only update their own company users"
            )

    # Get the update data as dict (only fields that were sent)
    update_data = user_update.model_dump(exclude_unset=True)

    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_user, key, value)

    # Update audit fields
    db_user.updated_by = current_user.id
    db_user.updated_at = datetime.now()

    # Commit changes
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user