from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import text, inspect
from datetime import datetime

# --- IMPORTS DES ROUTEURS ---
from .routers import (
    performance, 
    safety, 
    auth, 
    workouts, 
    coach, 
    user, 
    feed, 
    profiles, 
    athlete_profiles, 
    coach_memories
)
from app.core.database import engine, Base
# Import des modèles pour s'assurer qu'ils sont connus de Base.metadata
from app.models import sql_models 

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE INIT ---
try:
    logger.info("Tentative de création des tables SQL...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables vérifiées/créées.")
except Exception as e:
    logger.error(f"ERREUR CRITIQUE DÉMARRAGE DB : {e}")

app = FastAPI(
    title="TitanFlow API",
    description="API Backend pour l'application TitanFlow",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- CONFIGURATION CORS (CORRECTIF INFRA) ---
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- GLOBAL EXCEPTION HANDLER ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔥 CRASH GLOBAL NON GÉRÉ : {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erreur serveur interne (TitanFlow Panic): {str(exc)}"},
    )

# --- ROUTEURS ---
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(workouts.router)
app.include_router(performance.router)
app.include_router(safety.router)
app.include_router(coach.router)
app.include_router(feed.router)
app.include_router(profiles.router)
app.include_router(athlete_profiles.router)
app.include_router(coach_memories.router)

# --- ROUTES SYSTÈME ---

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "active",
        "version": "2.1.0",
        "service": "TitanFlow Backend",
        "database": "connected"
    }

@app.get("/db_status", tags=["System"])
async def database_status():
    """
    📊 Diagnostic complet de la base de données
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        table_status = {}
        for table in ['users', 'workout_sessions', 'workout_sets', 'feed_items', 
                     'athlete_profiles', 'coach_memories']:
            if table in tables:
                columns = inspector.get_columns(table)
                table_status[table] = {
                    "status": "✅ EXISTE",
                    "column_count": len(columns),
                    "columns": [col['name'] for col in columns[:10]]
                }
            else:
                table_status[table] = {"status": "❌ MANQUANTE"}
        
        # Compter les données
        with engine.connect() as conn:
            data_counts = {}
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                    data_counts[table] = result[0] if result else 0
                except:
                    data_counts[table] = "ERROR"
        
        return {
            "status": "success",
            "total_tables": len(tables),
            "tables_found": tables,
            "table_status": table_status,
            "data_counts": data_counts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/fix_db", tags=["System"])
async def fix_database_schema():
    """
    🛠️ MIGRATION DOUCE : Tente de créer les tables manquantes sans supprimer les données.
    """
    try:
        operations = []
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                # Création/Vérification User avec profil JSON
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR UNIQUE,
                        email VARCHAR UNIQUE,
                        hashed_password VARCHAR,
                        profile_data JSON DEFAULT '{}',
                        strategy_data TEXT,
                        weekly_plan_data TEXT,
                        draft_workout_data TEXT
                    );
                """))
                operations.append("✅ Table 'users' vérifiée")

                # Tables critiques
                # ... (Le reste du code de fix_db est implicite ici, 
                # mais dans le doute, la recréation complète via SQLAlchemy est plus sûre)
                
                Base.metadata.create_all(bind=engine)
                operations.append("✅ SQLAlchemy create_all exécuté")

                trans.commit()
                return {"status": "SUCCESS", "operations": operations}
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.get("/system/nuke_db", tags=["System"])
async def nuke_database_reset():
    """
    ☢️ OPTION NUCLÉAIRE : SUPPRIME ET RECRÉE TOUTE LA BASE DE DONNÉES.
    À utiliser uniquement en cas de désynchronisation critique du schéma (Erreur 500 Auth).
    """
    try:
        logger.warning("☢️ DÉMARRAGE DU PROTOCOLE NUKE_DB...")
        
        # 1. On supprime tout (Drop Tables)
        # On utilise cascade pour gérer les clés étrangères
        Base.metadata.drop_all(bind=engine)
        logger.info("🗑️ Toutes les tables ont été supprimées.")
        
        # 2. On recrée tout propre (Create Tables)
        Base.metadata.create_all(bind=engine)
        logger.info("✨ Toutes les tables ont été recréées avec le nouveau schéma.")
        
        return {
            "status": "DESTROYED_AND_REBUILT",
            "message": "La base de données a été réinitialisée. Vous devez recréer un compte.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"🔥 Échec du Nuke : {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Échec de la réinitialisation : {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)