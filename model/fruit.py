from typing import Any

from sqlalchemy import Table, Column, Integer, String, MetaData
from model.model import Base

class Fruit(Base):
   __tablename__ = 'fruits'
   
   id = Column(Integer, primary_key=True)
   name = Column(String)
   quantity = Column(Integer)
