from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.config import get_env_variable

db_user = get_env_variable("DB_USER")
db_password = get_env_variable("DB_PASSWORD")
db_read = get_env_variable("DB_READ")
db_main = get_env_variable("DB_MAIN")


# Create SQLAlchemy engine and session
def get_db_engine():
    """
    Creates and returns a SQLAlchemy engine for connecting to the PostgreSQL database.

    Returns:
        sqlalchemy.engine.Engine: A SQLAlchemy engine instance using configured credentials.
    """

    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_read}/{db_main}"
    return create_engine(db_url)


def get_db_session():
    """
    Creates and returns a new SQLAlchemy session for database operations.

    Returns:
        sqlalchemy.orm.Session: A new session bound to the database engine.
    """

    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()
