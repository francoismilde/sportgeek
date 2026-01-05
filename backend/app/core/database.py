from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 1. On récupère l'URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Sécurité : si pas d'URL, on met du SQLite temporaire
if not SQLALCHEMY_DATABASE_URL:
    print("⚠️ DATABASE_URL absente. Mode SQLite temporaire.")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# 3. Correctif pour l'URL (postgres -> postgresql)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 4. Création du moteur (Version Simplifiée pour éviter les Timeouts)
connect_args = {}
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args
    # On a retiré pool_pre_ping pour tester la connexion brute
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()