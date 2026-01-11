from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import text 

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
    version="2.1.0", # Bump version pour Migration V2
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

# --- GLOBAL EXCEPTION HANDLER (ANTI-CRASH) ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔥 CRASH GLOBAL NON GÉRÉ : {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erreur serveur interne (TitanFlow Panic): {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )

# --- ROUTEURS ---
app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(performance.router)
app.include_router(safety.router)
app.include_router(coach.router)
app.include_router(user.router)
app.include_router(feed.router)
app.include_router(profiles.router)
app.include_router(athlete_profiles.router)
app.include_router(coach_memories.router)

# --- ROUTE SPÉCIALE DE RÉPARATION (SELF-REPAIR V5 - MIGRATION COMPLETE) ---
@app.get("/fix_db", tags=["System"])
def fix_database_schema():
    """
    🛠️ ROUTE D'URGENCE V5 : Création des tables V2 + Patch des colonnes.
    Lancez cette URL pour mettre à jour la BDD sur Render.
    """
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            
            # 1. CRÉATION DES TABLES V2 (Si elles n'existent pas)
            
            # Table Profil Athlète
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS athlete_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    basic_info JSON DEFAULT '{}',
                    physical_metrics JSON DEFAULT '{}',
                    sport_context JSON DEFAULT '{}',
                    performance_baseline JSON DEFAULT '{}',
                    injury_prevention JSON DEFAULT '{}',
                    training_preferences JSON DEFAULT '{}',
                    goals JSON DEFAULT '{}',
                    constraints JSON DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            
            # Table Mémoire Coach
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS coach_memories (
                    id SERIAL PRIMARY KEY,
                    athlete_profile_id INTEGER UNIQUE REFERENCES athlete_profiles(id) ON DELETE CASCADE,
                    metadata_info JSON DEFAULT '{}',
                    current_context JSON DEFAULT '{}',
                    response_patterns JSON DEFAULT '{}',
                    performance_baselines JSON DEFAULT '{}',
                    adaptation_signals JSON DEFAULT '{}',
                    sport_specific_insights JSON DEFAULT '{}',
                    training_history_summary JSON DEFAULT '{}',
                    athlete_preferences JSON DEFAULT '{}',
                    coach_notes JSON DEFAULT '{}',
                    memory_flags JSON DEFAULT '{}',
                    last_updated TIMESTAMPTZ DEFAULT NOW()
                );
            """))

            # 2. PATCH DES TABLES EXISTANTES (Colonnes manquantes)
            
            # Table USERS
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS strategy_data TEXT;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_plan_data TEXT;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS draft_workout_data TEXT;"))

            # Table WORKOUT_SESSIONS
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS energy_level INTEGER DEFAULT 5;"))
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS notes TEXT;"))
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();"))
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS ai_analysis TEXT;"))
            
            # Table WORKOUT_SETS
            connection.execute(text("ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS metric_type VARCHAR DEFAULT 'LOAD_REPS';"))
            connection.execute(text("ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS rest_seconds INTEGER DEFAULT 0;"))
            
            trans.commit()
            return {
                "status": "SUCCESS", 
                "message": "✅ Base de données migrée : Tables 'athlete_profiles' et 'coach_memories' créées + Colonnes ajoutées !"
            }
            
    except Exception as e:
        return {"status": "ERROR", "message": f"❌ Erreur lors de la migration : {str(e)}"}


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {
        "status": "active",
        "version": "2.1.0",
        "service": "TitanFlow Backend",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)