from typing import List

from sqlalchemy.ext.asyncio import AsyncSession  
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from fastapi import FastAPI, Depends, HTTPException

from database import init_db, get_session
from models import Licenses, Packages

app = FastAPI(title="FastAPI + Supabase Postgres")

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/packages", response_model=List[Packages])
async def get_packages(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Packages))
    return result.scalars().all()

@app.post("/packages", response_model=Packages, status_code=201)
async def create_package(package: Packages, session: AsyncSession = Depends(get_session)):
    session.add(package)
    try:
        await session.commit()
        await session.refresh(package)
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="Package already exists") from ie
    return package


@app.get("/licenses", response_model=List[Licenses])
async def get_licenses(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Licenses))
    return result.scalars().all()

@app.get("/")
async def root():
    return {"message": "FastAPI connected to Supabase Postgres!"}