from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class OrderOut(BaseModel):
    id: int
    name: str
    item: str
    phone: str
    status: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderCreated(BaseModel):
    id: int
    status: str
    notification: Optional[str] = None


class CustomerInfo(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class OrderInfo(BaseModel):
    type: Optional[str] = None  # e.g. 'delivery' or 'pickup'
    time: Optional[str] = None  # keep as string like '2:45 PM' for human readable
    date: Optional[str] = None  # keep as string like 'Oct 26, 2025'


class Address(BaseModel):
    street: Optional[str] = None
    apartment: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    full: Optional[str] = None  # fallback free-form address


class OrderItem(BaseModel):
    name: str
    quantity: Optional[int] = 1
    price: Optional[Decimal] = None


class OrderDetail(BaseModel):
    id: Optional[int] = None
    customer: CustomerInfo
    order: OrderInfo
    delivery_address: Optional[Address] = None
    items: List[OrderItem]
    total: Optional[Decimal] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
