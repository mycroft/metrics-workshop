from typing import Any
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def get_base() -> Any:
    return Base
