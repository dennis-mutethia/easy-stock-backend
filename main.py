from typing import List

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession  
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from fastapi import Body, FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from auth import authenticate_user, create_access_token, get_current_user
from database import init_db, get_session
from models import Licenses, Packages, Shops, Users, Companies

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Easy-Stock Backend", lifespan=lifespan)

@app.post("/login")
async def login(
    phone: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(phone, password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id, 
            "name": user.name, 
            "phone": user.phone
        }
    }

@app.get("/me")
async def me(current_user: Users = Depends(get_current_user)):
    return current_user

@app.get("/packages", response_model=List[Packages])
async def get_packages(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Packages))
    return result.scalars().all()

@app.post("/packages", response_model=Packages, status_code=201)
async def create_package(
    package: Packages, 
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    session.add(package)
    try:
        await session.commit()
        await session.refresh(package)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="Package already exists") from ie
    return package

# PATCH endpoint to partially update a Package
@app.patch("/packages/{package_id}", response_model=Packages, status_code=200)
async def update_package(
    package_id: int,
    package_update: Packages,  # This will only include fields sent in the request body
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
        if key not in {"id", "created_at", "created_by"}:  # Protect audit fields
            setattr(db_package, key, value)

    # Update audit fields
    from datetime import datetime
    db_package.updated_at = datetime.now()
    db_package.updated_by = current_user.id

    # Commit changes
    session.add(db_package)
    await session.commit()
    await session.refresh(db_package)

    return db_package

@app.get("/licenses", response_model=List[Licenses])
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

@app.post("/licenses", response_model=Licenses, status_code=201)
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

@app.get("/companies")
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

@app.post("/companies", response_model=Companies, status_code=201)
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

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/docs")