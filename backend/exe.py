#!/usr/bin/env python3
"""
Script de mise à jour des tables et dépendances manquantes pour TitanFlow
Corrige les problèmes de schéma et prépare l'environnement
"""

import os
import sys
import json
import logging
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le chemin du backend
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

def load_environment():
    """Charge les variables d'environnement"""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info("✅ Variables d'environnement chargées")
    else:
        logger.warning("⚠️ Fichier .env non trouvé, utilisation des variables système")
    
    # Récupérer l'URL de la base de données
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    
    # Correction pour PostgreSQL
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    return DATABASE_URL

def check_database_schema(engine):
    """Vérifie et corrige le schéma de la base de données"""
    logger.info("🔍 Vérification du schéma de base de données...")
    
    required_tables = [
        "users",
        "workout_sessions",
        "workout_sets",
        "feed_items",
        "athlete_profiles",
        "coach_memories"
    ]
    
    required_columns = {
        "users": [
            "id", "username", "email", "hashed_password",
            "profile_data", "strategy_data", "weekly_plan_data", "draft_workout_data"
        ],
        "workout_sessions": [
            "id", "user_id", "date", "duration", "rpe", "energy_level",
            "notes", "ai_analysis", "created_at"
        ],
        "workout_sets": [
            "id", "session_id", "exercise_name", "set_order", "weight",
            "reps", "rpe", "rest_seconds", "metric_type"
        ],
        "athlete_profiles": [
            "id", "user_id", "basic_info", "physical_metrics", "sport_context",
            "performance_baseline", "injury_prevention", "training_preferences",
            "goals", "constraints", "created_at", "updated_at"
        ],
        "coach_memories": [
            "id", "athlete_profile_id", "metadata_info", "current_context",
            "response_patterns", "performance_baselines", "adaptation_signals",
            "sport_specific_insights", "training_history_summary", 
            "athlete_preferences", "coach_notes", "memory_flags", "last_updated"
        ],
        "feed_items": [
            "id", "user_id", "type", "title", "message", "action_payload",
            "is_read", "is_completed", "priority", "created_at"
        ]
    }
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Créer les tables manquantes
        for table in required_tables:
            if table not in existing_tables:
                logger.info(f"📦 Création de la table '{table}'...")
                try:
                    create_table_sql = get_table_creation_sql(table)
                    conn.execute(text(create_table_sql))
                    conn.commit()
                    logger.info(f"✅ Table '{table}' créée")
                except Exception as e:
                    logger.error(f"❌ Erreur création table '{table}': {e}")
        
        # Vérifier et ajouter les colonnes manquantes
        for table, columns in required_columns.items():
            if table in existing_tables:
                existing_columns = [col['name'] for col in inspector.get_columns(table)]
                for column in columns:
                    if column not in existing_columns:
                        logger.info(f"➕ Ajout colonne '{column}' à la table '{table}'...")
                        try:
                            alter_sql = get_column_addition_sql(table, column)
                            conn.execute(text(alter_sql))
                            conn.commit()
                            logger.info(f"✅ Colonne '{column}' ajoutée")
                        except Exception as e:
                            logger.warning(f"⚠️ Impossible d'ajouter la colonne '{column}': {e}")

def get_table_creation_sql(table_name):
    """Retourne le SQL pour créer une table spécifique"""
    sql_statements = {
        "users": """
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
        """,
        "workout_sessions": """
            CREATE TABLE workout_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                date DATE NOT NULL,
                duration FLOAT NOT NULL,
                rpe FLOAT NOT NULL,
                energy_level INTEGER DEFAULT 5,
                notes TEXT,
                ai_analysis TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "workout_sets": """
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
        """,
        "athlete_profiles": """
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
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "coach_memories": """
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
                last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "feed_items": """
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
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """
    }
    
    return sql_statements.get(table_name, "")

def get_column_addition_sql(table_name, column_name):
    """Retourne le SQL pour ajouter une colonne spécifique"""
    column_definitions = {
        "users": {
            "profile_data": "ALTER TABLE users ADD COLUMN profile_data TEXT;",
            "strategy_data": "ALTER TABLE users ADD COLUMN strategy_data TEXT;",
            "weekly_plan_data": "ALTER TABLE users ADD COLUMN weekly_plan_data TEXT;",
            "draft_workout_data": "ALTER TABLE users ADD COLUMN draft_workout_data TEXT;",
        },
        "workout_sessions": {
            "energy_level": "ALTER TABLE workout_sessions ADD COLUMN energy_level INTEGER DEFAULT 5;",
            "notes": "ALTER TABLE workout_sessions ADD COLUMN notes TEXT;",
            "ai_analysis": "ALTER TABLE workout_sessions ADD COLUMN ai_analysis TEXT;",
            "created_at": "ALTER TABLE workout_sessions ADD COLUMN created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;",
        },
        "workout_sets": {
            "metric_type": "ALTER TABLE workout_sets ADD COLUMN metric_type VARCHAR DEFAULT 'LOAD_REPS';",
            "rest_seconds": "ALTER TABLE workout_sets ADD COLUMN rest_seconds INTEGER DEFAULT 0;",
        }
    }
    
    table_cols = column_definitions.get(table_name, {})
    return table_cols.get(column_name, f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT;")

def create_indexes(engine):
    """Crée les indexes nécessaires"""
    logger.info("🔧 Création des indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id ON workout_sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_workout_sessions_date ON workout_sessions(date);",
        "CREATE INDEX IF NOT EXISTS idx_workout_sets_session_id ON workout_sets(session_id);",
        "CREATE INDEX IF NOT EXISTS idx_athlete_profiles_user_id ON athlete_profiles(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_coach_memories_profile_id ON coach_memories(athlete_profile_id);",
        "CREATE INDEX IF NOT EXISTS idx_feed_items_user_id ON feed_items(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_feed_items_type ON feed_items(type);",
        "CREATE INDEX IF NOT EXISTS idx_feed_items_created_at ON feed_items(created_at);",
    ]
    
    with engine.connect() as conn:
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                conn.commit()
                logger.info(f"✅ Index créé: {idx_sql[:50]}...")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de créer l'index: {e}")

def check_dependencies():
    """Vérifie les dépendances Python requises"""
    logger.info("📦 Vérification des dépendances...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "psycopg2-binary",
        "python-dotenv",
        "pandas",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "google-generativeai",
        "pydantic",
    ]
    
    try:
        import pkg_resources
        installed_packages = {pkg.key for pkg in pkg_resources.working_set}
        
        missing_packages = []
        for package in required_packages:
            # Extraire le nom de base du package
            base_package = package.split('[')[0].split('>')[0].split('<')[0].split('=')[0].strip()
            if base_package not in installed_packages:
                missing_packages.append(package)
        
        if missing_packages:
            logger.warning(f"⚠️ Packages manquants: {', '.join(missing_packages)}")
            logger.info("💡 Installation recommandée: pip install " + " ".join(missing_packages))
        else:
            logger.info("✅ Toutes les dépendances sont installées")
            
    except ImportError:
        logger.warning("⚠️ Impossible de vérifier les dépendances (pkg_resources non disponible)")

def fix_schemas_file():
    """Corrige le fichier schemas.py pour la classe CoachMemoryResponse"""
    schemas_path = BASE_DIR / "app" / "models" / "schemas.py"
    if not schemas_path.exists():
        logger.warning(f"⚠️ Fichier schemas.py introuvable: {schemas_path}")
        return
    
    logger.info("🔧 Correction du fichier schemas.py...")
    
    try:
        with open(schemas_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Recherche et correction de la classe CoachMemoryResponse
        if 'class CoachMemoryResponse' in content:
            # Pattern pour trouver la classe
            import re
            pattern = r'(class CoachMemoryResponse\(BaseModel\):.*?)(?=^\s*class|\Z)'
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            
            if match:
                class_content = match.group(1)
                
                # Remplacer la ligne problématique
                fixed_class_content = re.sub(
                    r'readiness_score: int = Field\(alias="current_context", default={}\)\.get\("readiness_score", 0\)',
                    'readiness_score: int = Field(default=0, alias="current_context")',
                    class_content
                )
                
                # Remplacer dans le contenu original
                content = content.replace(class_content, fixed_class_content)
                
                # Écrire le fichier corrigé
                with open(schemas_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info("✅ Fichier schemas.py corrigé")
            else:
                logger.warning("⚠️ Impossible de trouver la classe CoachMemoryResponse dans schemas.py")
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction de schemas.py: {e}")

def create_sample_data(engine):
    """Crée des données de test si la base est vide"""
    logger.info("🎨 Création de données de test...")
    
    with engine.connect() as conn:
        # Vérifier si des utilisateurs existent
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        if user_count == 0:
            logger.info("👤 Création d'un utilisateur de test...")
            conn.execute(text("""
                INSERT INTO users (username, email, hashed_password)
                VALUES ('testuser', 'test@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW')
            """))
            
            # Récupérer l'ID de l'utilisateur
            result = conn.execute(text("SELECT id FROM users WHERE username = 'testuser'"))
            user_id = result.scalar()
            
            # Créer un profil athlète
            logger.info("🏋️ Création d'un profil athlète de test...")
            conn.execute(text(f"""
                INSERT INTO athlete_profiles (
                    user_id, basic_info, physical_metrics, sport_context,
                    goals, training_preferences
                ) VALUES (
                    {user_id},
                    '{{\"pseudo\": \"TestAthlete\", \"email\": \"test@example.com\"}}',
                    '{{\"weight\": 75, \"height\": 180}}',
                    '{{\"sport\": \"Musculation\", \"level\": \"Intermédiaire\"}}',
                    '{{\"primary_goal\": \"Prise de muscle\"}}',
                    '{{\"duration_min\": 60, \"preferred_split\": \"Full Body\"}}'
                )
            """))
            
            conn.commit()
            logger.info("✅ Données de test créées")

def main():
    """Fonction principale"""
    print("""
╔══════════════════════════════════════════╗
║   TITANFLOW DATABASE SETUP & FIX         ║
╚══════════════════════════════════════════╝
    """)
    
    try:
        # 1. Charger l'environnement
        DATABASE_URL = load_environment()
        logger.info(f"📊 Connexion à la base de données: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
        
        # 2. Créer le moteur SQLAlchemy
        engine = create_engine(DATABASE_URL)
        
        # 3. Vérifier les dépendances
        check_dependencies()
        
        # 4. Corriger le fichier schemas.py
        fix_schemas_file()
        
        # 5. Vérifier et corriger le schéma de la base de données
        check_database_schema(engine)
        
        # 6. Créer les indexes
        create_indexes(engine)
        
        # 7. Créer des données de test (optionnel)
        create_sample_data(engine)
        
        print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 SETUP TERMINÉ AVEC SUCCÈS !
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Prochaines étapes:
1. Redémarrez le serveur: uvicorn app.main:app --reload
2. Accédez à l'interface: http://localhost:8000/docs
3. Testez la route /health pour vérifier la connexion

Pour tester avec un utilisateur:
• Username: testuser
• Password: password123
        """)
        
    except Exception as e:
        logger.error(f"❌ ERREUR CRITIQUE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()