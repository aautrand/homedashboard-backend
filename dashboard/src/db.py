from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase


def create_session(app):
    DATABASE_URL = f"postgresql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}"
    engine = create_engine(DATABASE_URL)

    session = scoped_session(sessionmaker(bind=engine))
    return session


class Base(DeclarativeBase):
    pass
