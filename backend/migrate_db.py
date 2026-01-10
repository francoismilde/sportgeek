import os
import json
import sqlalchemy
from sqlalchemy import text, inspect
from dotenv import load_dotenv
import logging
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charge les variables locales
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Correction pour Render qui utilise parfois postgres:// au lieu de postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    logger.error("❌ Erreur : Pas de DATABASE_URL trouvée.")
    # Fallback SQLite pour le local si pas de variable d'env
    DATABASE_URL = "sqlite:///./sql_app.db"
    logger.warning(f"⚠️  Utilisation de la BDD par défaut : {DATABASE_URL}")

logger.info(f"🔌 Connexion à la BDD...")
engine = sqlalchemy.create_engine(DATABASE_URL)

def table_exists(connection, table_name):
    """Vérifie si une table existe"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def column_exists(connection, table_name, column_name):
    """Vérifie si une colonne existe dans une table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def apply_migration():
    """Applique toutes les migrations nécessaires (Structure + Données)"""
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            logger.info("🛠️ Début des migrations de structure...")
            
            # --- 1. TABLES CORE (EXISTANTES) ---
            
            # Users
            if not table_exists(connection, "users"):
                logger.info("Création table 'users'...")
                connection.execute(text("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR UNIQUE NOT NULL,
                        email VARCHAR UNIQUE,
                        hashed_password VARCHAR NOT NULL,
                        profile_data TEXT,
                        strategy_data TEXT,
                        weekly_plan_data TEXT,
                        draft_workout_data TEXT
                    );
                """))
            
            # Workout Sessions
            if not table_exists(connection, "workout_sessions"):
                logger.info("Création table 'workout_sessions'...")
                connection.execute(text("""
                    CREATE TABLE workout_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        date DATE NOT NULL,
                        duration FLOAT NOT NULL,
                        rpe FLOAT NOT NULL,
                        energy_level INTEGER DEFAULT 5,
                        notes TEXT,
                        ai_analysis TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
            
            # Workout Sets
            if not table_exists(connection, "workout_sets"):
                logger.info("Création table 'workout_sets'...")
                connection.execute(text("""
                    CREATE TABLE workout_sets (
                        id SERIAL PRIMARY KEY,
                        session_id INTEGER REFERENCES workout_sessions(id) ON DELETE CASCADE,
                        exercise_name VARCHAR NOT NULL,
                        set_order INTEGER NOT NULL,
                        weight FLOAT DEFAULT 0.0,
                        reps FLOAT DEFAULT 0.0,
                        rpe FLOAT DEFAULT 0.0,
                        rest_seconds INTEGER DEFAULT 0,
                        metric_type VARCHAR DEFAULT 'LOAD_REPS'
                    );
                """))

            # Feed Items
            if not table_exists(connection, "feed_items"):
                logger.info("Création table 'feed_items'...")
                connection.execute(text("""
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

            # --- 2. NOUVELLES TABLES V2 (TITANFLOW PRO - LE FIX EST ICI) ---

            # Athlete Profiles
            if not table_exists(connection, "athlete_profiles"):
                logger.info("🆕 Création table 'athlete_profiles' (V2)...")
                # Utilisation de TEXT pour SQLite/Postgres compatibility simple sur le JSON
                connection.execute(text("""
                    CREATE TABLE athlete_profiles (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                        basic_info TEXT DEFAULT '{}',
                        physical_metrics TEXT DEFAULT '{}',
                        sport_context TEXT DEFAULT '{}',
                        performance_baseline TEXT DEFAULT '{}',
                        injury_prevention TEXT DEFAULT '{}',
                        training_preferences TEXT DEFAULT '{}',
                        goals TEXT DEFAULT '{}',
                        constraints TEXT DEFAULT '{}',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
                logger.info("✅ Table 'athlete_profiles' créée.")

            # Coach Memories
            if not table_exists(connection, "coach_memories"):
                logger.info("🆕 Création table 'coach_memories' (V2)...")
                connection.execute(text("""
                    CREATE TABLE coach_memories (
                        id SERIAL PRIMARY KEY,
                        athlete_profile_id INTEGER UNIQUE REFERENCES athlete_profiles(id) ON DELETE CASCADE,
                        metadata_info TEXT DEFAULT '{}',
                        current_context TEXT DEFAULT '{}',
                        response_patterns TEXT DEFAULT '{}',
                        performance_baselines TEXT DEFAULT '{}',
                        adaptation_signals TEXT DEFAULT '{}',
                        sport_specific_insights TEXT DEFAULT '{}',
                        training_history_summary TEXT DEFAULT '{}',
                        athlete_preferences TEXT DEFAULT '{}',
                        coach_notes TEXT DEFAULT '{}',
                        memory_flags TEXT DEFAULT '{}',
                        last_updated TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
                logger.info("✅ Table 'coach_memories' créée.")

            # --- 3. MIGRATION DES COLONNES MANQUANTES (FIX CRITIQUE) ---
            
            if table_exists(connection, "users"):
                migrations_users = [
                    ("email", "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;"), # <--- IMPORTANT POUR LE WIZARD
                    ("profile_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"),
                    ("strategy_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS strategy_data TEXT;"),
                    ("weekly_plan_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_plan_data TEXT;"),
                    ("draft_workout_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS draft_workout_data TEXT;"),
                ]
                for col_name, sql in migrations_users:
                    if not column_exists(connection, "users", col_name):
                        logger.info(f"Ajout colonne '{col_name}' -> 'users'")
                        connection.execute(text(sql))

            # --- 4. FIN ---
            trans.commit()
            logger.info("🎉 Toutes les migrations (Structure V2) sont terminées !")
            return True
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ CRASH MIGRATION : {str(e)}")
            return False

if __name__ == "__main__":
    logger.info("🚀 Lancement TitanFlow DB Migrator...")
    success = apply_migration()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)