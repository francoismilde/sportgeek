from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

# Récupération de l'URL de connexion
# Si pas de variable, on met une sqlite temporaire pour éviter que ça crash au démarrage
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# Création du moteur
# connect_args={"check_same_thread": False} est nécessaire seulement pour SQLite
connect_args = {}
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

# Création de la session (l'espace de travail pour la BDD)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# La classe de base pour nos futurs modèles (Tables)
Base = declarative_base()

# Dépendance pour récupérer la DB dans chaque endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()