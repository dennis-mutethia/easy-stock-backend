from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from utils.models import Product_Categories, Users
from utils.database import get_session
from routes.auth import get_current_user

router = APIRouter(prefix="/products/categories", tags=["Product Categories"])

@router.get("/")
async def get_product_categories(
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    statement = select(Product_Categories).where(Product_Categories.shop_id == current_user.shop_id)

    result = await session.execute(statement)
    product_categories = result.scalars().all()

    if not product_categories:
        raise HTTPException(status_code=404, detail="No product Categories found")

    return product_categories


@router.get("/{product_category_id}")
async def get_product_category(
    product_category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    statement = (
        select(Product_Categories)
        .where(Product_Categories.shop_id == current_user.shop_id)
        .where(Product_Categories.id == product_category_id)
    )

    result = await session.execute(statement)
    product_category = result.scalar_one_or_none()

    if not product_category:
        raise HTTPException(status_code=404, detail="Product Category not found")

    return product_category

@router.post("/", response_model=Product_Categories, status_code=201)
async def create_product_category(
    product_category: Product_Categories, 
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    
    # Only super-admin, admins & supervisors (user_level_id in 0, 1, 2) can create product categories
    if current_user.user_level_id not in [0, 1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin, admin & supervisor can create product categories"
        )

    session.add(product_category)
    try:
        await session.commit()
        await session.refresh(product_category)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="Product Category already exists") from ie
    return product_category


@router.patch("/{product_category_id}", response_model=Product_Categories)
async def update_product_category(
    product_category_id: int,
    product_category_update: Product_Categories,
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):

    # Only super-admin, admins & supervisors (user_level_id in 0, 1, 2) can update product categories
    if current_user.user_level_id not in [0, 1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admin, admin & supervisor can update product categories"
        )

    # Fetch the existing product category
    statement = (
        select(Product_Categories)
        .where(Product_Categories.shop_id == current_user.shop_id)
        .where(Product_Categories.id == product_category_id)
    )

    result = await session.execute(statement)
    db_product_category = result.scalar_one_or_none()

    if not db_product_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Category not found"
        )

    # Get the update data as dict (only fields that were sent)
    update_data = product_category_update.model_dump(exclude_unset=True)

    # Update fields (excluding protected ones like id, created_at, etc.)
    for key, value in update_data.items():
        if key not in {"id", "created_at", "created_by", "updated_at", "updated_by"}:  # Protect audit fields
            setattr(db_product_category, key, value)

    # Update audit fields
    db_product_category.updated_by = current_user.id
    db_product_category.updated_at = datetime.now()
    # Commit changes
    session.add(db_product_category)
    await session.commit()
    await session.refresh(db_product_category)

    return db_product_category