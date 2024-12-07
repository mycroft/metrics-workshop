from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utils.random import get_random_quantity

def create_db_engine():
    return create_engine('postgresql://demo:demo@localhost:5432/demo', echo=True)

def get_session(engine):
    # Simulate a database connection timeout
    if get_random_quantity == 7:
        raise TimeoutError("Database connection timed out")

    Session = sessionmaker(bind=engine)
    return Session()

def create_schema(base, engine):
    base.metadata.create_all(engine)