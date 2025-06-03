from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_engine(username, password, database_name):
    db_url = f"mysql+pymysql://{username}:{password}@127.0.0.1:3306/{database_name}"
    return create_engine(db_url, echo=True)

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

def get_faker():
    from faker import Faker
    fake = Faker("pl_PL")
    return fake