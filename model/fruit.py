from typing import Any

from sqlalchemy import Table, Column, Integer, String
from sqlalchemy import func
from model.model import Base

class Fruit(Base):
   __tablename__ = 'fruits'
   
   id = Column(Integer, primary_key=True)
   name = Column(String)
   quantity = Column(Integer)

def get_total_quantity(session, fruit_name: str) -> int:
    total_quantity = session.query(func.sum(Fruit.quantity)).filter(Fruit.name == fruit_name).scalar()
    return total_quantity if total_quantity is not None else 0

def get_possible_fruits() -> Any:
    return ['apples', 'oranges', 'bananas', 'grapes', 'pears']