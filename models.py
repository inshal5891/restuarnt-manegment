# models.py
from sqlalchemy import Column, Integer, String, DateTime, func
from db import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    item = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    status = Column(String, default="received")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
