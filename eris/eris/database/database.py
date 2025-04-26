import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get database configuration from environment variables
DB_TYPE = os.getenv("JANO_DB_TYPE", "sqlite").lower()
DB_HOST = os.getenv("JANO_DB_HOST", "localhost")
DB_PORT = os.getenv("JANO_DB_PORT", "5432")
DB_USER = os.getenv("JANO_DB_USER", "postgres")
DB_PASSWORD = os.getenv("JANO_DB_PASSWORD", "postgres")
DB_NAME = os.getenv("JANO_DB_NAME", "jano_eris")
SQLITE_PATH = os.getenv("JANO_SQLITE_PATH", "jano_eris.db")

# Configure database URL based on type
if DB_TYPE == "postgres":
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    # SQLite by default
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_PATH}"

# Create database engine
if DB_TYPE == "sqlite":
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create local session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for declarative models
Base = declarative_base()

# Function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()