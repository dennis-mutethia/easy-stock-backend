from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from utils.models import Products, Users
from utils.database import get_session
from routes.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/")
async def get_products(
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    statement = select(Products).where(Products.shop_id == current_user.shop_id)

    result = await session.execute(statement)
    products = result.scalars().all()

    if not products:
        raise HTTPException(status_code=404, detail="No products found")

    return products


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    statement = (
        select(Products)
        .where(Products.shop_id == current_user.shop_id)
        .where(Products.id == product_id)
    )

    result = await session.execute(statement)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.post("/", response_model=Products, status_code=201)
async def create_product(
    product: Products, 
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    
    # Only super-admin, admins & supervisors (user_level_id in 0, 1, 2) can create products
    if current_user.user_level_id not in [0, 1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin, admin & supervisor can create products"
        )

    session.add(product)
    try:
        await session.commit()
        await session.refresh(product)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="Product already exists") from ie
    return product


@router.patch("/{product_id}", response_model=Products)
async def update_product(
    product_id: int,
    product_update: Products,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):

    # Only super-admin, admins & supervisors (user_level_id in 0, 1, 2) can update products
    if current_user.user_level_id not in [0, 1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin, admin & supervisor can update products"
        )

    # Fetch the existing product
    statement = (
        select(Products)
        .where(Products.shop_id == current_user.shop_id)
        .where(Products.id == product_id)
    )

    result = await session.execute(statement)
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Get the update data as dict (only fields that were sent)
    update_data = product_update.model_dump(exclude_unset=True)

    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_product, key, value)

    # Update audit fields
    db_product.updated_by = current_user.id
    db_product.updated_at = datetime.now()
    # Commit changes
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)

    return db_product