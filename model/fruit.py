from datetime import timedelta
from typing import Any

from sqlalchemy import Table, Column, Integer, String, DateTime
from sqlalchemy import func
from model.model import Base

class Fruit(Base):
    __tablename__ = 'fruits'
   
    id = Column(Integer, primary_key=True)
    name = Column(String)
    quantity = Column(Integer)

    created_at = Column(DateTime, default=func.now())

def get_recent_quantity(session, fruit_name: str) -> int:
    total_quantity = session.query(func.sum(Fruit.quantity)) \
        .filter(Fruit.name == fruit_name) \
        .filter(Fruit.created_at > func.now() - timedelta(minutes=1)) \
        .scalar()

    return total_quantity if total_quantity is not None else 0

def get_all_fruits(session) -> int:
    all_quantity = session \
        .query(func.sum(Fruit.quantity)) \
        .filter(Fruit.created_at > func.now() - timedelta(minutes=1)) \
        .scalar()

    return all_quantity if all_quantity is not None else 0

def get_possible_fruits() -> Any:
    return ['apples', 'oranges', 'bananas', 'grapes', 'pears']
