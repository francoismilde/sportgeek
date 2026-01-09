import os
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
    sys.exit(1)

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
    """Applique toutes les migrations nécessaires"""
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            logger.info("🛠️ Début des migrations...")
            
            # 1. CRÉATION DES TABLES DE BASE (si elles n'existent pas)
            
            # Table users
            if not table_exists(connection, "users"):
                logger.info("Création de la table 'users'...")
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
                logger.info("✅ Table 'users' créée.")
            
            # Table workout_sessions
            if not table_exists(connection, "workout_sessions"):
                logger.info("Création de la table 'workout_sessions'...")
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
                logger.info("✅ Table 'workout_sessions' créée.")
            
            # Table workout_sets
            if not table_exists(connection, "workout_sets"):
                logger.info("Création de la table 'workout_sets'...")
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
                logger.info("✅ Table 'workout_sets' créée.")
            
            # Table feed_items
            if not table_exists(connection, "feed_items"):
                logger.info("Création de la table 'feed_items'...")
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
                logger.info("✅ Table 'feed_items' créée.")
            
            # 2. MIGRATIONS POUR LES COLONNES MANQUANTES (si tables existent)
            
            # Migration pour users
            if table_exists(connection, "users"):
                migrations_users = [
                    ("profile_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"),
                    ("strategy_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS strategy_data TEXT;"),
                    ("weekly_plan_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_plan_data TEXT;"),
                    ("draft_workout_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS draft_workout_data TEXT;"),
                ]
                
                for col_name, sql in migrations_users:
                    if not column_exists(connection, "users", col_name):
                        logger.info(f"Ajout de la colonne '{col_name}' à la table 'users'...")
                        connection.execute(text(sql))
                        logger.info(f"✅ Colonne '{col_name}' ajoutée.")
            
            # Migration pour workout_sessions
            if table_exists(connection, "workout_sessions"):
                migrations_sessions = [
                    ("energy_level", "ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS energy_level INTEGER DEFAULT 5;"),
                    ("notes", "ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS notes TEXT;"),
                    ("created_at", "ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();"),
                    ("ai_analysis", "ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS ai_analysis TEXT;"),  # <-- LA COLONNE MANQUANTE
                ]
                
                for col_name, sql in migrations_sessions:
                    if not column_exists(connection, "workout_sessions", col_name):
                        logger.info(f"Ajout de la colonne '{col_name}' à la table 'workout_sessions'...")
                        connection.execute(text(sql))
                        logger.info(f"✅ Colonne '{col_name}' ajoutée.")
            
            # Migration pour workout_sets
            if table_exists(connection, "workout_sets"):
                migrations_sets = [
                    ("metric_type", "ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS metric_type VARCHAR DEFAULT 'LOAD_REPS';"),
                    ("rest_seconds", "ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS rest_seconds INTEGER DEFAULT 0;"),
                ]
                
                for col_name, sql in migrations_sets:
                    if not column_exists(connection, "workout_sets", col_name):
                        logger.info(f"Ajout de la colonne '{col_name}' à la table 'workout_sets'...")
                        connection.execute(text(sql))
                        logger.info(f"✅ Colonne '{col_name}' ajoutée.")
            
            # 3. CRÉATION DES INDEX POUR LES PERFORMANCES
            logger.info("Création des index...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id ON workout_sessions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_workout_sessions_date ON workout_sessions(date);",
                "CREATE INDEX IF NOT EXISTS idx_workout_sets_session_id ON workout_sets(session_id);",
                "CREATE INDEX IF NOT EXISTS idx_feed_items_user_id ON feed_items(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_feed_items_created_at ON feed_items(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_feed_items_type ON feed_items(type);",
            ]
            
            for idx_sql in indexes:
                try:
                    connection.execute(text(idx_sql))
                except Exception as e:
                    logger.warning(f"⚠️ Impossible de créer l'index: {e}")
            
            trans.commit()
            logger.info("🎉 Toutes les migrations ont été appliquées avec succès !")
            
            # 4. VÉRIFICATION FINALE
            logger.info("🔍 Vérification finale des colonnes...")
            check_tables = ["users", "workout_sessions", "workout_sets", "feed_items"]
            
            for table in check_tables:
                if table_exists(connection, table):
                    inspector = inspect(engine)
                    columns = inspector.get_columns(table)
                    logger.info(f"Table '{table}' a {len(columns)} colonnes:")
                    for col in columns:
                        logger.info(f"  - {col['name']} ({col['type']})")
            
            return True
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Erreur lors de la migration : {str(e)}")
            return False

if __name__ == "__main__":
    logger.info("🚀 Lancement du script de migration de la base de données...")
    
    success = apply_migration()
    
    if success:
        logger.info("✅ Migration terminée avec succès !")
        sys.exit(0)
    else:
        logger.error("❌ La migration a échoué.")
        sys.exit(1)