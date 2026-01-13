from typing import Optional
from sqlmodel import SQLModel, Field

class Packages(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    amount: float
    pay: float
    validity: int = None
    color: str = None
    description: Optional[str] = None
    offer: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

class Licenses(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str
    package_id: int
    expires_at: int = None
    payment_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None    
    
class Companies(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    license_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None    
    
class ShopTypes(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

class Shops(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    location: str = None
    company_id: int = None
    shop_type_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None
    phone_1: Optional[str] = None
    phone_2: Optional[str] = None
    paybill: Optional[str] = None
    account_no: Optional[str] = None
    till_no: Optional[str] = None

class UserLevels(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    level: int = 0
    description: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone: str
    shop_id: int = None
    user_level_id: int = 0
    password: str
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

class ProductCategories(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    shop_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None    

class Products(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    purchase_price: float = None
    selling_price: float = None
    category_id: int = None
    shop_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

class Customers(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone: str
    shop_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

class PaymentModes(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

class Cashbox(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: Optional[str] = None
    cash: float = None
    mpesa: float = None
    shop_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None
    
class Stock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stock_date: Optional[str] = None
    product_id: int
    shop_id: int
    purchase_price: float = None
    selling_price: float = None
    opening: float = None
    additions: float = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

class Bills(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = None
    total: float = None
    paid: float = None
    shop_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

class Expenses(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: Optional[str] = None
    name: str
    amount: float = None
    shop_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None
    
class Payments(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bill_id: int = None
    amount: float = None
    payment_mode_id: int = None
    shop_id: int = None
    created_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

