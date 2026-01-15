from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import text, inspect, create_engine
from datetime import datetime

from app.core.database import engine, Base
# Import des modèles
from app.models import sql_models 

# --- IMPORTS DES ROUTEURS ---
from .routers import (
    performance, 
    safety, 
    auth, 
    workouts, 
    coach, 
    user, 
    feed,
    athlete_profiles,
    coach_memories  # ✅ NOUVEL IMPORT CRITIQUE (DEV-CARD #01)
)

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE INIT ---
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables SQL vérifiées.")
except Exception as e:
    logger.error(f"ERREUR INIT DB : {e}")

app = FastAPI(
    title="TitanFlow API",
    description="API Backend pour l'application TitanFlow",
    version="2.5.0", # Bump version pour marquer le changement
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- CONFIGURATION CORS ---
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
    logger.error(f"🔥 CRASH : {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erreur serveur : {str(exc)}"},
    )

# --- ROUTEURS ACTIFS ---

# 1. Auth
app.include_router(auth.router)

# 2. PROFILES & MEMORY
app.include_router(
    athlete_profiles.router, 
    prefix="/api/v1/profiles", 
    tags=["Profiles"]
)

# ✅ AJOUT DU ROUTEUR MÉMOIRE (DEV-CARD #02)
# Les préfixes sont déjà définis dans le routeur lui-même (/api/v1/coach-memories)
app.include_router(coach_memories.router)

# 3. Autres features
app.include_router(workouts.router)
app.include_router(performance.router)
app.include_router(safety.router)
app.include_router(coach.router)
app.include_router(feed.router)

# --- ROUTES SYSTÈME ---

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "active",
        "version": "2.5.0",
        "database": "connected"
    }

@app.get("/db_status", tags=["System"])
async def database_status():
    """Diagnostic DB"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        columns_user = []
        if 'users' in tables:
            columns_user = [c['name'] for c in inspector.get_columns('users')]
            
        return {
            "status": "success",
            "tables": tables,
            "json_profile_ready": 'profile_data' in columns_user,
            "engrams_ready": 'coach_engrams' in tables, # ✅ Check Engrams
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)