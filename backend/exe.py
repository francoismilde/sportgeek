import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Charger les variables d'env pour l'URL de la DB
load_dotenv(os.path.join("backend", ".env"))

def get_db_url():
    # Récupérer l'URL ou utiliser SQLite par défaut si non défini
    db_url = os.getenv("DATABASE_URL", "sqlite:///backend/sql_app.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url

def check_and_migrate():
    print("🛡️  VÉRIFICATION DU SCHÉMA DE LA BASE DE DONNÉES...")
    
    url = get_db_url()
    print(f"   🎯 Cible : {url}")
    
    engine = create_engine(url)
    inspector = inspect(engine)
    
    # Colonnes requises pour le Profil Riche (ISO Prod)
    required_columns = [
        "performance_baseline", 
        "injury_prevention", 
        "constraints", 
        "training_preferences",
        "goals",
        "sport_context",
        "physical_metrics",
        "basic_info"
    ]

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Vérifier si la table existe
            if not inspector.has_table("athlete_profiles"):
                print("   ⚠️ Table 'athlete_profiles' inexistante.")
                print("   🛠️ Création de la table complète...")
                
                # Création propre compatible Postgres/SQLite
                is_postgres = "postgresql" in url
                json_type = "JSONB" if is_postgres else "JSON" # SQLite gère JSON comme TEXT ou JSON selon version, mais SQLAlchemy gère le mapping.
                
                # Pour le SQL brut, on utilise TEXT pour SQLite pour être sûr, JSONB pour PG
                sql_type = "JSONB" if is_postgres else "TEXT"

                conn.execute(text(f"""
                    CREATE TABLE athlete_profiles (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER UNIQUE,
                        basic_info {sql_type} DEFAULT '{{}}',
                        physical_metrics {sql_type} DEFAULT '{{}}',
                        sport_context {sql_type} DEFAULT '{{}}',
                        performance_baseline {sql_type} DEFAULT '{{}}',
                        injury_prevention {sql_type} DEFAULT '{{}}',
                        training_preferences {sql_type} DEFAULT '{{}}',
                        goals {sql_type} DEFAULT '{{}}',
                        constraints {sql_type} DEFAULT '{{}}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                print("   ✅ Table 'athlete_profiles' créée avec succès.")
            
            else:
                print("   ✅ Table 'athlete_profiles' trouvée. Vérification des colonnes...")
                # 2. Vérifier les colonnes manquantes
                existing_columns = [col['name'] for col in inspector.get_columns("athlete_profiles")]
                
                for col in required_columns:
                    if col not in existing_columns:
                        print(f"   ➕ Ajout de la colonne manquante : {col}...")
                        
                        is_postgres = "postgresql" in url
                        col_type = "JSONB" if is_postgres else "TEXT" # Safe fallback for SQLite
                        
                        conn.execute(text(f"ALTER TABLE athlete_profiles ADD COLUMN {col} {col_type} DEFAULT '{{}}'"))
                        print(f"      ✅ Colonne {col} ajoutée.")
                    else:
                        print(f"      🆗 {col} existe déjà.")

            trans.commit()
            print("\n✨ BASE DE DONNÉES SYNCHRONISÉE ET PRÊTE !")
            print("   Toutes les données du Labo, Matrice et Santé seront bien sauvegardées.")

        except Exception as e:
            trans.rollback()
            print(f"\n❌ ERREUR CRITIQUE : {e}")
            if "duplicate column" in str(e):
                print("   (C'est probablement juste une fausse alerte, la colonne existait déjà).")

if __name__ == "__main__":
    check_and_migrate()