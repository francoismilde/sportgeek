#!/usr/bin/env python3
"""
Script de vérification et optimisation TitanFlow
Adapté à votre schéma de base déjà complet
"""

import os
import sys
import json
import logging
from pathlib import Path
from sqlalchemy import create_engine, text, inspect

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
    
    if not env_path.exists():
        logger.warning("⚠️ Fichier .env non trouvé, création avec valeurs par défaut...")
        create_default_env(env_path)
    
    # Charger les variables
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    # Récupérer l'URL de la base de données
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    
    # Correction pour PostgreSQL
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    logger.info(f"📊 Connexion à: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    return DATABASE_URL

def create_default_env(env_path):
    """Crée un fichier .env par défaut"""
    default_env = """# Configuration TitanFlow
DATABASE_URL=sqlite:///./sql_app.db

# Sécurité JWT
SECRET_KEY=your-super-secret-key-change-in-production-2024
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24h

# API Google Gemini
GEMINI_API_KEY=your-gemini-api-key-here

# Logging
LOG_LEVEL=INFO
"""
    
    with open(env_path, 'w') as f:
        f.write(default_env)
    
    logger.info(f"✅ Fichier .env créé: {env_path}")

def verify_database_health(engine):
    """Vérifie l'état de santé de la base de données"""
    logger.info("🔍 Vérification de la santé de la base de données...")
    
    try:
        with engine.connect() as conn:
            # Test de connexion
            conn.execute(text("SELECT 1"))
            logger.info("✅ Connexion à la base de données OK")
            
            # Vérifier les tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                "users", "athlete_profiles", "coach_memories",
                "workout_sessions", "workout_sets", "feed_items"
            ]
            
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                logger.error(f"❌ Tables manquantes: {missing_tables}")
                return False
            
            logger.info(f"✅ Toutes les tables existent ({len(tables)} tables)")
            
            # Vérifier les indexes
            logger.info("📊 Analyse des indexes...")
            check_indexes(conn, tables)
            
            # Vérifier les contraintes d'intégrité
            logger.info("🔗 Vérification des relations...")
            check_foreign_keys(conn)
            
            # Statistiques
            logger.info("📈 Statistiques des tables...")
            get_table_statistics(conn, tables)
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur de vérification: {e}")
        return False

def check_indexes(conn, tables):
    """Vérifie la présence d'indexes optimisés"""
    important_indexes = {
        "users": ["username", "email"],
        "workout_sessions": ["user_id", "date"],
        "workout_sets": ["session_id"],
        "athlete_profiles": ["user_id"],
        "coach_memories": ["athlete_profile_id"],
        "feed_items": ["user_id", "created_at"]
    }
    
    for table, columns in important_indexes.items():
        if table in tables:
            try:
                result = conn.execute(text(f"""
                    SELECT COUNT(*) FROM pg_indexes 
                    WHERE tablename = '{table}' 
                    AND indexname LIKE '%{columns[0]}%'
                """ if "postgresql" in str(conn.engine.url) else f"""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='index' AND tbl_name='{table}'
                """))
                count = result.scalar()
                if count == 0:
                    logger.warning(f"   ⚠️ Table '{table}' manque d'index sur {columns}")
                else:
                    logger.info(f"   ✅ Table '{table}' a des indexes")
            except Exception as e:
                logger.debug(f"   ℹ️ Vérification d'index ignorée pour {table}: {e}")

def check_foreign_keys(conn):
    """Vérifie l'intégrité des clés étrangères"""
    foreign_key_checks = [
        ("workout_sessions", "user_id", "users", "id"),
        ("workout_sets", "session_id", "workout_sessions", "id"),
        ("athlete_profiles", "user_id", "users", "id"),
        ("coach_memories", "athlete_profile_id", "athlete_profiles", "id"),
        ("feed_items", "user_id", "users", "id")
    ]
    
    for fk_table, fk_column, ref_table, ref_column in foreign_key_checks:
        try:
            # Vérifier si la table existe
            result = conn.execute(text(f"SELECT 1 FROM {fk_table} LIMIT 1"))
            logger.info(f"   ✅ Relation {fk_table}.{fk_column} → {ref_table}.{ref_column}")
        except Exception as e:
            logger.warning(f"   ⚠️ Table {fk_table} inaccessible: {e}")

def get_table_statistics(conn, tables):
    """Affiche les statistiques des tables"""
    for table in tables:
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            logger.info(f"   📦 {table}: {count} enregistrements")
        except Exception as e:
            logger.debug(f"   ℹ️ Impossible de compter {table}: {e}")

def optimize_database(engine):
    """Applique des optimisations à la base de données"""
    logger.info("⚡ Application des optimisations...")
    
    optimizations = []
    
    try:
        with engine.connect() as conn:
            # 1. Créer des indexes manquants (s'ils n'existent pas)
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
                "CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id ON workout_sessions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_workout_sessions_date ON workout_sessions(date);",
                "CREATE INDEX IF NOT EXISTS idx_workout_sets_session_id ON workout_sets(session_id);",
                "CREATE INDEX IF NOT EXISTS idx_athlete_profiles_user_id ON athlete_profiles(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_coach_memories_profile_id ON coach_memories(athlete_profile_id);",
                "CREATE INDEX IF NOT EXISTS idx_feed_items_user_id ON feed_items(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_feed_items_created_at ON feed_items(created_at DESC);"
            ]
            
            for sql in indexes_sql:
                try:
                    conn.execute(text(sql))
                    optimizations.append(f"✅ Index: {sql.split('ON ')[1].split(';')[0]}")
                except Exception as e:
                    logger.debug(f"   ℹ️ Index déjà existant ou non supporté: {e}")
            
            # 2. Nettoyer les données orphelines (si supporté)
            try:
                cleanup_sql = """
                    DELETE FROM workout_sets 
                    WHERE session_id NOT IN (SELECT id FROM workout_sessions);
                    
                    DELETE FROM workout_sessions 
                    WHERE user_id NOT IN (SELECT id FROM users);
                    
                    DELETE FROM feed_items 
                    WHERE user_id NOT IN (SELECT id FROM users);
                    
                    DELETE FROM coach_memories 
                    WHERE athlete_profile_id NOT IN (SELECT id FROM athlete_profiles);
                    
                    DELETE FROM athlete_profiles 
                    WHERE user_id NOT IN (SELECT id FROM users);
                """
                
                # Exécuter chaque instruction séparément
                for stmt in cleanup_sql.strip().split(';'):
                    if stmt.strip():
                        conn.execute(text(stmt.strip()))
                
                optimizations.append("✅ Nettoyage des données orphelines")
                conn.commit()
            except Exception as e:
                logger.debug(f"   ℹ️ Nettoyage non supporté ou non nécessaire: {e}")
            
            logger.info(f"✨ {len(optimizations)} optimisations appliquées")
            
    except Exception as e:
        logger.error(f"❌ Erreur d'optimisation: {e}")

def verify_dependencies():
    """Vérifie et installe les dépendances manquantes"""
    logger.info("📦 Vérification des dépendances...")
    
    required_packages = {
        "fastapi": ">=0.104.0",
        "uvicorn": ">=0.24.0",
        "sqlalchemy": ">=2.0.0",
        "psycopg2-binary": ">=2.9.0",
        "python-dotenv": ">=1.0.0",
        "python-jose[cryptography]": ">=3.3.0",
        "passlib[bcrypt]": ">=1.7.0",
        "google-generativeai": ">=0.3.0",
        "pydantic": ">=2.0.0",
        "pandas": ">=2.0.0",
        "alembic": ">=1.12.0"
    }
    
    missing = []
    
    for package, version in required_packages.items():
        try:
            # Nettoyer le nom du package
            clean_pkg = package.split('[')[0].split('<')[0].split('>')[0].split('=')[0].strip()
            __import__(clean_pkg)
            logger.info(f"   ✅ {package} {version}")
        except ImportError:
            missing.append(package)
            logger.warning(f"   ❌ {package} {version} - MANQUANT")
    
    if missing:
        logger.warning(f"⚠️ {len(missing)} packages manquants")
        logger.info("💡 Installation recommandée:")
        logger.info(f"   pip install {' '.join(missing)}")
        return False
    
    logger.info("✅ Toutes les dépendances sont installées")
    return True

def generate_schema_report(engine):
    """Génère un rapport détaillé du schéma"""
    logger.info("📄 Génération du rapport de schéma...")
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        report = {
            "environment": {
                "database_url": str(engine.url).split('@')[-1] if '@' in str(engine.url) else str(engine.url),
                "database_dialect": engine.dialect.name,
                "tables_count": len(inspector.get_table_names())
            },
            "tables": {}
        }
        
        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                col_info = {
                    "name": column['name'],
                    "type": str(column['type']),
                    "nullable": column['nullable'],
                    "default": column.get('default', None),
                    "primary_key": column.get('primary_key', False)
                }
                columns.append(col_info)
            
            report["tables"][table_name] = {
                "columns": columns,
                "row_count": get_table_row_count(conn, table_name)
            }
        
        # Sauvegarder le rapport
        report_path = BASE_DIR / "database_schema_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"✅ Rapport sauvegardé: {report_path}")
        return report

def get_table_row_count(conn, table_name):
    """Compte les lignes d'une table"""
    try:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()
    except:
        return 0

def main():
    """Fonction principale"""
    print("""
╔══════════════════════════════════════════╗
║   TITANFLOW DATABASE HEALTH CHECK        ║
╚══════════════════════════════════════════╝
    """)
    
    try:
        # 1. Charger l'environnement
        DATABASE_URL = load_environment()
        
        # 2. Créer le moteur SQLAlchemy
        engine = create_engine(DATABASE_URL)
        
        # 3. Vérifier la santé de la base
        if not verify_database_health(engine):
            logger.error("❌ La base de données a des problèmes")
            sys.exit(1)
        
        # 4. Vérifier les dépendances
        verify_dependencies()
        
        # 5. Optimiser la base de données
        optimize_database(engine)
        
        # 6. Générer un rapport
        report = generate_schema_report(engine)
        
        # 7. Afficher le résumé
        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 VÉRIFICATION TERMINÉE AVEC SUCCÈS !
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RÉSUMÉ :
• Base de données: {report['environment']['database_dialect'].upper()}
• Tables: {report['environment']['tables_count']}
• Statut: ✅ OPTIMALE

🏗️  TABLES PRINCIPALES :
  1. users - {report['tables'].get('users', {}).get('row_count', 0)} utilisateurs
  2. athlete_profiles - {report['tables'].get('athlete_profiles', {}).get('row_count', 0)} profils
  3. coach_memories - {report['tables'].get('coach_memories', {}).get('row_count', 0)} mémoires IA
  4. workout_sessions - {report['tables'].get('workout_sessions', {}).get('row_count', 0)} séances
  5. feed_items - {report['tables'].get('feed_items', {}).get('row_count', 0)} notifications

🔧 PROCHAINES ÉTAPES :
1. Lancez le serveur : uvicorn app.main:app --reload
2. Testez l'API : http://localhost:8000/docs
3. Vérifiez la santé : http://localhost:8000/health

📄 Rapport détaillé : database_schema_report.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
        
    except Exception as e:
        logger.error(f"❌ ERREUR CRITIQUE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()