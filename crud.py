# crud.py
from db import SessionLocal
from models import Order
from typing import List
from sqlalchemy.exc import SQLAlchemyError


def create_order(name: str, item: str, phone: str) -> Order:
    """Create and return an Order. Raises RuntimeError on DB errors."""
    try:
        with SessionLocal() as session:
            order = Order(name=name, item=item, phone=phone)
            session.add(order)
            session.commit()
            session.refresh(order)
            return order
    except SQLAlchemyError as exc:
        # Log as needed and raise a generic error for the caller to handle
        raise RuntimeError(f"database error creating order: {exc}") from exc


def get_orders(limit: int = 50) -> List[Order]:
    """Return recent orders. Raises RuntimeError on DB errors."""
    try:
        with SessionLocal() as session:
            return (
                session.query(Order).order_by(Order.created_at.desc()).limit(limit).all()
            )
    except SQLAlchemyError as exc:
        raise RuntimeError(f"database error fetching orders: {exc}") from exc
