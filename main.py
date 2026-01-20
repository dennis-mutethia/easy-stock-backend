
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from utils.database import init_db
from routes import companies, licenses, packages, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Easy-Stock Backend", 
    lifespan=lifespan
)

# Include all routers
app.include_router(auth.router)
app.include_router(packages.router)
app.include_router(licenses.router)
app.include_router(companies.router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/docs")