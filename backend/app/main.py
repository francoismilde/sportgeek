from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import text 

# --- IMPORTS DES ROUTEURS ---
# [MODIFICATION] Ajout de 'feed'
from app.routers import performance, safety, auth, workouts, coach, user, feed, profiles, profiles, athlete_profiles, coach_memories
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
    version="2.0.0", # Neural Feed v2 - AthleteProfile version="1.9.4", # Bump Neural Feed CoachMemory
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
# [MODIFICATION] Activation du Feed
app.include_router(feed.router)
app.include_router(profiles.router)
app.include_router(profiles.router)
app.include_router(athlete_profiles.router)
app.include_router(coach_memories.router)

# --- ROUTE SPÉCIALE DE RÉPARATION (SELF-REPAIR V4) ---
@app.get("/fix_db", tags=["System"])
def fix_database_schema():
    """
    🛠️ ROUTE D'URGENCE V4 : Ajoute TOUTES les colonnes manquantes.
    Inclus maintenant draft_workout_data pour réparer le crash Login.
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
            
            # Mémoire IA
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS strategy_data TEXT;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_plan_data TEXT;"))
            
            # [FIX CRITIQUE] Ajout du brouillon
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS draft_workout_data TEXT;"))
            
            trans.commit()
            return {
                "status": "SUCCESS", 
                "message": "✅ Base de données réparée : Colonne 'draft_workout_data' ajoutée !"
            }
            
    except Exception as e:
        return {"status": "ERROR", "message": f"❌ Erreur lors de la réparation : {str(e)}"}


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {
        "status": "active",
        "version": "1.9.4",
        "service": "TitanFlow Backend",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)