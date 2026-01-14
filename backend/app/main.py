from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import text, inspect, create_engine
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
    athlete_profiles  # ✅ Uniquement le nouveau routeur unifié
)
from app.core.database import engine, Base
# Import des modèles
from app.models import sql_models 

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
    version="2.4.1", 
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

# 1. Auth (inchangé)
app.include_router(auth.router)

# 2. PROFILES - UNIQUE ROUTEUR UNIFIÉ
# Supprimez l'inclusion de l'ancien routeur profiles.router
app.include_router(
    athlete_profiles.router, 
    prefix="/api/v1/profiles",  # ✅ Préfixe unique pour toutes les routes
    tags=["Profiles"]
)

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
        "version": "2.4.1",
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
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/system/migrate", tags=["System"])
async def run_surgical_migration():
    """
    🚑 MIGRATION CHIRURGICALE (Via API)
    """
    try:
        logs = []
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                inspector = inspect(engine)
                existing_tables = inspector.get_table_names()
                
                # 1. Users & JSON
                if 'users' in existing_tables:
                    cols = [c['name'] for c in inspector.get_columns('users')]
                    if 'profile_data' not in cols:
                        is_postgres = "postgres" in str(engine.url)
                        col_type = "JSONB" if is_postgres else "JSON"
                        if not is_postgres: col_type = "TEXT" 

                        conn.execute(text(f"ALTER TABLE users ADD COLUMN profile_data {col_type} DEFAULT '{{}}'"))
                        logs.append(f"✅ Colonne profile_data ({col_type}) ajoutée.")
                    else:
                        logs.append("ℹ️ Colonne profile_data déjà présente.")
                
                # 2. Nettoyage
                for old_table in ['coach_memories', 'athlete_profiles']:
                    if old_table in existing_tables:
                        conn.execute(text(f"DROP TABLE {old_table} CASCADE"))
                        logs.append(f"🗑️ Table {old_table} supprimée.")
                
                # 3. Feed Items
                if 'feed_items' not in existing_tables:
                    conn.execute(text("""
                        CREATE TABLE feed_items (
                            id VARCHAR PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            type VARCHAR NOT NULL,
                            title VARCHAR NOT NULL,
                            message VARCHAR NOT NULL,
                            action_payload TEXT,
                            is_read BOOLEAN DEFAULT FALSE,
                            is_completed BOOLEAN DEFAULT FALSE,
                            priority INTEGER DEFAULT 1,
                            created_at TIMESTAMPTZ DEFAULT NOW()
                        );
                    """))
                    logs.append("✅ Table feed_items créée.")
                
                trans.commit()
                return {"status": "SUCCESS", "logs": logs}
                
            except Exception as inner_e:
                trans.rollback()
                raise inner_e
                
    except Exception as e:
        return {"status": "ERROR", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)