import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL")

# Railway requires SSL, local development might not
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    # Add SSL mode for Railway PostgreSQL (non-local hosts)
    if parsed.hostname and not parsed.hostname.startswith(("localhost", "127.0.0.1", "db", "postgres")):
        # Production/Railway - force SSL
        connect_args = {"sslmode": "require"}
    else:
        connect_args = {}
else:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,    # Recycle connections after 5 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
