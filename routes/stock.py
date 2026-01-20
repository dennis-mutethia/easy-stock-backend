from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from utils.models import Stock, Users
from utils.database import get_session
from routes.auth import get_current_user

router = APIRouter(prefix="/stock", tags=["Stock"])

@router.get("/")
async def get_stocks(
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    statement = select(Stock).where(Stock.shop_id == current_user.shop_id)

    result = await session.execute(statement)
    stocks = result.scalars().all()
    
    print(stocks)

    if not stocks:
        raise HTTPException(status_code=404, detail="No stocks found")

    return stocks


@router.get("/{stock_id}")
async def get_stock(
    stock_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    statement = (
        select(Stock)
        .where(Stock.shop_id == current_user.shop_id)
        .where(Stock.id == stock_id)
    )

    result = await session.execute(statement)
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    return stock


@router.get("/filter/{stock_date}")
async def get_stock_by_date(
    stock_date: str,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    
    #convert stock_date string to date object
    stock_date = datetime.strptime(stock_date, "%Y-%m-%d").date()
    
    if not stock_date:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")    
    
    statement = (
        select(Stock)
        .where(Stock.shop_id == current_user.shop_id)
        .where(Stock.stock_date == stock_date)
    )
    
    result = await session.execute(statement)
    stocks = result.scalars().all()

    if not stocks:
        raise HTTPException(status_code=404, detail="No Stock found")

    return stocks


@router.post("/", response_model=Stock, status_code=201)
async def create_stock(
    Stock: Stock, 
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    
    # Only super-admin, admins & supervisors (user_level_id in 0, 1, 2) can create Stock
    if current_user.user_level_id not in [0, 1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin, admin & supervisor can create Stock"
        )

    session.add(Stock)
    try:
        await session.commit()
        await session.refresh(Stock)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="Stock already exists") from ie
    return Stock


@router.patch("/{stock_id}", response_model=Stock)
async def update_stock(
    stock_id: int,
    stock_update: Stock,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):

    # Only super-admin, admins & supervisors (user_level_id in 0, 1, 2) can update Stock
    if current_user.user_level_id not in [0, 1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin, admin & supervisor can update Stock"
        )

    # Fetch the existing Stock
    statement = (
        select(Stock)
        .where(Stock.shop_id == current_user.shop_id)
        .where(Stock.id == stock_id)
    )

    result = await session.execute(statement)
    db_Stock = result.scalar_one_or_none()

    if not db_Stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )

    # Get the update data as dict (only fields that were sent)
    update_data = stock_update.model_dump(exclude_unset=True)

    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_Stock, key, value)

    # Update audit fields
    db_Stock.updated_by = current_user.id
    db_Stock.updated_at = datetime.now()
    # Commit changes
    session.add(db_Stock)
    await session.commit()
    await session.refresh(db_Stock)

    return db_Stock