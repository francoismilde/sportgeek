from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Charge les variables du fichier .env (utile uniquement en local)
load_dotenv()

# --- 1. RÉCUPÉRATION DE L'URL ---
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Si aucune URL n'est configurée, on prévient (évite le piège du SQLite silencieux en prod)
if not SQLALCHEMY_DATABASE_URL:
    print("⚠️  ATTENTION: DATABASE_URL non trouvée. Utilisation de SQLite temporaire.")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
else:
    # --- 2. CORRECTIF "FIX" POUR RENDER/SUPABASE ---
    # SQLAlchemy a besoin de 'postgresql+psycopg2://' mais Supabase donne souvent 'postgres://' ou 'postgresql://'
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# --- 3. CONFIGURATION DU MOTEUR (ENGINE) ---
connect_args = {}

# Si on est sur SQLite (Local sans config)
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
else:
    # Si on est sur PostgreSQL (Supabase/Render)
    # On ajoute un pool_pre_ping pour éviter que la connexion ne "meure" silencieusement
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True
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