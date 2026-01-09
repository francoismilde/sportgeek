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

def migrate_v1_to_v2_data(connection):
    """
    Migre les données de l'ancien format (User.profile_data) 
    vers le nouveau format (AthleteProfile + CoachMemory).
    """
    logger.info("🔄 Vérification de la migration des données V1 -> V2...")
    
    # Récupérer les utilisateurs qui n'ont pas encore de profil V2
    # On vérifie s'il existe une entrée dans athlete_profiles pour chaque user
    sql_check = text("""
        SELECT u.id, u.username, u.email, u.profile_data 
        FROM users u 
        LEFT JOIN athlete_profiles ap ON u.id = ap.user_id 
        WHERE ap.id IS NULL
    """)
    
    result = connection.execute(sql_check)
    users_to_migrate = result.fetchall()
    
    if not users_to_migrate:
        logger.info("✅ Toutes les données utilisateurs sont déjà migrées.")
        return

    logger.info(f"🚀 Migration de {len(users_to_migrate)} profils utilisateurs...")
    
    migrated_count = 0
    for u in users_to_migrate:
        try:
            # 1. Parsing de l'ancien JSON (s'il existe)
            old_data = {}
            if u.profile_data:
                try:
                    old_data = json.loads(u.profile_data)
                except:
                    logger.warning(f"⚠️ JSON invalide pour user {u.username}, utilisation par défaut.")
            
            # 2. Construction des nouvelles structures JSON
            # On mappe les anciens champs vers la nouvelle architecture
            basic_info = json.dumps({
                "pseudo": u.username, 
                "email": u.email,
                "training_age": old_data.get("experience_years", 0)
            })
            
            physical_metrics = json.dumps({
                "weight": float(old_data.get("weight", 0) or 0), 
                "height": float(old_data.get("height", 0) or 0),
                "body_fat": None
            })
            
            sport_context = json.dumps({
                "sport": old_data.get("sport", "Autre"), 
                "level": old_data.get("level", "Intermédiaire"),
                "position": old_data.get("position", None)
            })
            
            goals = json.dumps({
                "primary_goal": old_data.get("goal", "Forme générale")
            })

            # 3. Insertion dans athlete_profiles
            # Note: On utilise des requêtes paramétrées pour la sécurité
            insert_profile_sql = text("""
                INSERT INTO athlete_profiles (user_id, basic_info, physical_metrics, sport_context, goals)
                VALUES (:uid, :bi, :pm, :sc, :gl)
                RETURNING id
            """)
            
            res = connection.execute(insert_profile_sql, {
                "uid": u.id, 
                "bi": basic_info, 
                "pm": physical_metrics, 
                "sc": sport_context,
                "gl": goals
            })
            
            # Récupération de l'ID généré pour lier la mémoire
            profile_id = res.scalar()
            
            # 4. Initialisation de CoachMemory (Valeurs par défaut)
            insert_memory_sql = text("""
                INSERT INTO coach_memories (athlete_profile_id, current_context, memory_flags, metadata_info)
                VALUES (:pid, :ctx, :flags, :meta)
            """)
            
            default_context = json.dumps({"readiness_score": 80, "phase": "Integration", "fatigue_state": "Fresh"})
            default_flags = json.dumps({"migrated_from_v1": True})
            default_meta = json.dumps({"created_via": "migration_script"})
            
            connection.execute(insert_memory_sql, {
                "pid": profile_id,
                "ctx": default_context,
                "flags": default_flags,
                "meta": default_meta
            })
            
            migrated_count += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur migration user {u.username} (ID: {u.id}): {e}")

    logger.info(f"✨ Succès : {migrated_count} profils migrés vers l'architecture V2.")


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

            # --- 2. NOUVELLES TABLES V2 (TITANFLOW PRO) ---

            # Athlete Profiles
            if not table_exists(connection, "athlete_profiles"):
                logger.info("🆕 Création table 'athlete_profiles' (V2)...")
                # Utilisation de JSON (compatible Postgres/SQLite via SQLAlchemy abstraction usually, 
                # mais en raw SQL on utilise JSON ou TEXT selon le moteur. Ici JSON est standard PG)
                connection.execute(text("""
                    CREATE TABLE athlete_profiles (
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
                logger.info("✅ Table 'athlete_profiles' créée.")

            # Coach Memories
            if not table_exists(connection, "coach_memories"):
                logger.info("🆕 Création table 'coach_memories' (V2)...")
                connection.execute(text("""
                    CREATE TABLE coach_memories (
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
                logger.info("✅ Table 'coach_memories' créée.")

            # --- 3. MIGRATION DES COLONNES MANQUANTES (LEGACY) ---
            
            if table_exists(connection, "users"):
                migrations_users = [
                    ("profile_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"),
                    ("strategy_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS strategy_data TEXT;"),
                    ("weekly_plan_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_plan_data TEXT;"),
                    ("draft_workout_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS draft_workout_data TEXT;"),
                ]
                for col_name, sql in migrations_users:
                    if not column_exists(connection, "users", col_name):
                        logger.info(f"Ajout colonne '{col_name}' -> 'users'")
                        connection.execute(text(sql))

            if table_exists(connection, "workout_sessions"):
                migrations_sessions = [
                    ("energy_level", "ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS energy_level INTEGER DEFAULT 5;"),
                    ("notes", "ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS notes TEXT;"),
                    ("created_at", "ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();"),
                    ("ai_analysis", "ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS ai_analysis TEXT;"),
                ]
                for col_name, sql in migrations_sessions:
                    if not column_exists(connection, "workout_sessions", col_name):
                        logger.info(f"Ajout colonne '{col_name}' -> 'workout_sessions'")
                        connection.execute(text(sql))

            if table_exists(connection, "workout_sets"):
                migrations_sets = [
                    ("metric_type", "ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS metric_type VARCHAR DEFAULT 'LOAD_REPS';"),
                    ("rest_seconds", "ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS rest_seconds INTEGER DEFAULT 0;"),
                ]
                for col_name, sql in migrations_sets:
                    if not column_exists(connection, "workout_sets", col_name):
                        logger.info(f"Ajout colonne '{col_name}' -> 'workout_sets'")
                        connection.execute(text(sql))

            # --- 4. INDEXATION ---
            logger.info("Optimisation des index...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id ON workout_sessions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_workout_sessions_date ON workout_sessions(date);",
                "CREATE INDEX IF NOT EXISTS idx_feed_items_user_id ON feed_items(user_id);",
                # Index V2
                "CREATE INDEX IF NOT EXISTS idx_athlete_profiles_user_id ON athlete_profiles(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_coach_memories_profile_id ON coach_memories(athlete_profile_id);"
            ]
            
            for idx_sql in indexes:
                try:
                    connection.execute(text(idx_sql))
                except Exception as e:
                    logger.warning(f"⚠️ Index existant ou erreur mineure: {e}")
            
            # --- 5. MIGRATION DES DONNÉES ---
            migrate_v1_to_v2_data(connection)

            trans.commit()
            logger.info("🎉 Toutes les migrations (Structure V2 + Données) sont terminées !")
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