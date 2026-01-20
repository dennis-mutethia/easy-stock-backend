
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from utils.database import init_db
from routes import auth, companies, licenses, packages, products, product_categories, shop_types, shops, stock, user_levels, users

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
app.include_router(companies.router)
app.include_router(licenses.router)
app.include_router(packages.router)
app.include_router(products.router)
app.include_router(product_categories.router)
app.include_router(shop_types.router)
app.include_router(shops.router)
app.include_router(stock.router)
app.include_router(user_levels.router)
app.include_router(users.router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/docs")