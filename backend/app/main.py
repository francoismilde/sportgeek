from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import text # <--- Pour le script de réparation

# --- IMPORTS DES ROUTEURS ---
from app.routers import performance, safety, auth, workouts, coach, user
from app.core.database import engine, Base

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
    version="1.9.1", # Petite montée de version pour marquer le coup
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTEURS ---
app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(performance.router)
app.include_router(safety.router)
app.include_router(coach.router)
app.include_router(user.router)

# --- ROUTE SPÉCIALE DE RÉPARATION (SELF-REPAIR V3) ---
@app.get("/fix_db", tags=["System"])
def fix_database_schema():
    """
    🛠️ ROUTE D'URGENCE V3 : Ajoute TOUTES les colonnes manquantes.
    Inclus maintenant les colonnes pour la mémoire de l'IA.
    """
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            
            # 1. Table WORKOUT_SESSIONS (Séances)
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS energy_level INTEGER DEFAULT 5;"))
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS notes TEXT;"))
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();"))
            
            # 2. Table WORKOUT_SETS (Séries)
            connection.execute(text("ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS metric_type VARCHAR DEFAULT 'LOAD_REPS';"))
            connection.execute(text("ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS rest_seconds INTEGER DEFAULT 0;"))
            
            # 3. Table USERS (Profil)
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"))
            
            # [NOUVEAU] FIX CRITIQUE : Mémoire IA
            # On ajoute les colonnes manquantes qui causent le crash
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS strategy_data TEXT;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_plan_data TEXT;"))
            
            trans.commit()
            return {
                "status": "SUCCESS", 
                "message": "✅ Base de données réparée : Colonnes IA (strategy_data, weekly_plan_data) ajoutées !"
            }
            
    except Exception as e:
        return {"status": "ERROR", "message": f"❌ Erreur lors de la réparation : {str(e)}"}


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {
        "status": "active",
        "version": "1.9.1",
        "service": "TitanFlow Backend",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)