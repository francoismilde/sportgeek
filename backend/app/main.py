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
# On autorise TOUT pour éviter les blocages Auth sur Cloud Workstations / Mobile
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Autorise POST, GET, OPTIONS, PUT, DELETE
    allow_headers=["*"], # Autorise Authorization, Content-Type
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
    🛠️ MIGRATION COMPLÈTE V7 : Crée toutes les tables manquantes
    """
    try:
        operations = []
        
        with engine.connect() as connection:
            # Commencer une transaction
            trans = connection.begin()
            
            try:
                # 1. CRÉATION DE LA TABLE users SI ELLE N'EXISTE PAS
                # Note: profile_data est JSON ici pour la V2
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
                operations.append("✅ Table 'users' vérifiée/créée")
                
                # 2. CRÉATION DE workout_sessions
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS workout_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        date DATE,
                        duration FLOAT,
                        rpe FLOAT,
                        energy_level INTEGER DEFAULT 5,
                        notes TEXT,
                        ai_analysis TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
                operations.append("✅ Table 'workout_sessions' vérifiée/créée")
                
                # 3. CRÉATION DE workout_sets
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS workout_sets (
                        id SERIAL PRIMARY KEY,
                        session_id INTEGER REFERENCES workout_sessions(id),
                        exercise_name VARCHAR,
                        set_order INTEGER,
                        weight FLOAT DEFAULT 0.0,
                        reps FLOAT DEFAULT 0.0,
                        rpe FLOAT DEFAULT 0.0,
                        rest_seconds INTEGER DEFAULT 0,
                        metric_type VARCHAR DEFAULT 'LOAD_REPS'
                    );
                """))
                operations.append("✅ Table 'workout_sets' vérifiée/créée")
                
                # 4. CRÉATION DE athlete_profiles
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
                operations.append("✅ Table 'athlete_profiles' vérifiée/créée")
                
                # 5. CRÉATION DE coach_memories
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
                operations.append("✅ Table 'coach_memories' vérifiée/créée")
                
                # 6. CRÉATION DE feed_items (CRITIQUE !)
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS feed_items (
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
                operations.append("✅ Table 'feed_items' vérifiée/créée")
                
                # 7. AJOUT DES COLONNES MANQUANTES (sans erreur si existent déjà)
                
                # Colonnes users
                user_columns = [
                    ("email", "VARCHAR UNIQUE"),
                    ("profile_data", "JSON DEFAULT '{}'"),
                    ("strategy_data", "TEXT"),
                    ("weekly_plan_data", "TEXT"),
                    ("draft_workout_data", "TEXT")
                ]
                
                for col_name, col_type in user_columns:
                    try:
                        connection.execute(text(f"""
                            ALTER TABLE users 
                            ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                        """))
                        operations.append(f"✅ Colonne 'users.{col_name}' vérifiée/ajoutée")
                    except Exception as e:
                        operations.append(f"⚠️  users.{col_name}: {str(e)[:50]}")
                
                # Colonnes workout_sessions
                workout_cols = [
                    ("energy_level", "INTEGER DEFAULT 5"),
                    ("notes", "TEXT"),
                    ("ai_analysis", "TEXT"),
                    ("created_at", "TIMESTAMPTZ DEFAULT NOW()")
                ]
                
                for col_name, col_type in workout_cols:
                    try:
                        connection.execute(text(f"""
                            ALTER TABLE workout_sessions 
                            ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                        """))
                        operations.append(f"✅ Colonne 'workout_sessions.{col_name}' vérifiée/ajoutée")
                    except Exception as e:
                        operations.append(f"⚠️  workout_sessions.{col_name}: {str(e)[:50]}")
                
                # Colonnes workout_sets
                sets_cols = [
                    ("rest_seconds", "INTEGER DEFAULT 0"),
                    ("metric_type", "VARCHAR DEFAULT 'LOAD_REPS'")
                ]
                
                for col_name, col_type in sets_cols:
                    try:
                        connection.execute(text(f"""
                            ALTER TABLE workout_sets 
                            ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                        """))
                        operations.append(f"✅ Colonne 'workout_sets.{col_name}' vérifiée/ajoutée")
                    except Exception as e:
                        operations.append(f"⚠️  workout_sets.{col_name}: {str(e)[:50]}")
                
                # Valider la transaction
                trans.commit()
                
                # VÉRIFICATION FINALE
                inspector = inspect(engine)
                tables_after = inspector.get_table_names()
                
                # Compter les tables critiques
                critical_tables = ['feed_items', 'athlete_profiles', 'coach_memories']
                missing_tables = [t for t in critical_tables if t not in tables_after]
                
                if missing_tables:
                    return {
                        "status": "PARTIAL",
                        "message": "⚠️ Certaines tables sont toujours manquantes",
                        "operations": operations,
                        "missing_tables": missing_tables,
                        "tables_found": tables_after
                    }
                else:
                    return {
                        "status": "SUCCESS",
                        "message": "🎉 Migration complète réussie !",
                        "operations": operations,
                        "total_tables": len(tables_after),
                        "critical_tables_present": critical_tables,
                        "next_step": "Accédez à /db_status pour vérifier"
                    }
                    
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"❌ Échec de la migration: {str(e)}",
            "error_type": type(e).__name__,
            "suggestion": "Vérifiez les logs et les permissions de la base de données"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)