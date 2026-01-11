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
    # profiles,          <-- DÉSACTIVÉ (Legacy)
    # athlete_profiles,  <-- DÉSACTIVÉ (Legacy)
    # coach_memories     <-- DÉSACTIVÉ (Legacy)
)
from app.core.database import engine, Base
# Import des modèles pour que SQLAlchemy les reconnaisse
from app.models import sql_models 

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE INIT (SÉCURISÉ) ---
try:
    # create_all est SÛR : il ne fait rien si les tables existent déjà.
    # Il ne modifie pas les colonnes existantes.
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables SQL vérifiées.")
except Exception as e:
    logger.error(f"ERREUR INIT DB : {e}")

app = FastAPI(
    title="TitanFlow API",
    description="API Backend pour l'application TitanFlow",
    version="2.3.0", 
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
app.include_router(auth.router)
app.include_router(user.router)
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
        "version": "2.3.0",
        "database": "connected"
    }

@app.get("/db_status", tags=["System"])
async def database_status():
    """Diagnostic DB"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Vérification spécifique pour la colonne profile_data
        columns_user = []
        if 'users' in tables:
            columns_user = [c['name'] for c in inspector.get_columns('users')]
            
        return {
            "status": "success",
            "tables": tables,
            "users_columns": columns_user,
            "json_profile_ready": 'profile_data' in columns_user,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)