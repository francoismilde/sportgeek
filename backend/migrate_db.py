#!/usr/bin/env python3
"""
SCRIPT DE MIGRATION SÉCURISÉ TITAN V2
Objectif : Ajouter le support JSON (profile_data) SANS casser l'existant.
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Ajouter le backend au path
sys.path.append(str(Path(__file__).parent))

load_dotenv()

def get_db_url():
    db_url = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url

def run_migration():
    print("🚀 DÉMARRAGE DE LA MIGRATION SÉCURISÉE...")
    
    engine = create_engine(get_db_url())
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            # --- ÉTAPE 1 : AJOUTER LA COLONNE JSON À USERS (CRITIQUE POUR AUTH.PY) ---
            print("\n1️⃣  Vérification de la table 'users'...")
            if 'users' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('users')]
                
                if 'profile_data' not in columns:
                    print("   ➕ Ajout de la colonne 'profile_data'...")
                    # Syntaxe compatible Postgres (JSONB) et SQLite (TEXT/JSON)
                    is_postgres = "postgresql" in str(engine.url)
                    col_type = "JSONB" if is_postgres else "JSON"
                    
                    # Fallback SQLite si besoin
                    if "sqlite" in str(engine.url): col_type = "TEXT" 

                    conn.execute(text(f"ALTER TABLE users ADD COLUMN profile_data {col_type} DEFAULT '{{}}'"))
                    print("   ✅ Colonne ajoutée avec succès.")
                else:
                    print("   ✅ Colonne 'profile_data' déjà présente.")
            else:
                print("   ⚠️ Table 'users' introuvable (sera créée au redémarrage via init_db).")

            # --- ÉTAPE 2 : PROTECTION DES TABLES EXISTANTES ---
            # On NE SUPPRIME PAS les tables tant que les modèles SQL les référencent encore.
            print("\n2️⃣  Vérification des tables historiques (Mode Non-Destructif)...")
            tables_to_check = ['coach_memories', 'athlete_profiles']
            
            for table in tables_to_check:
                if table in existing_tables:
                    print(f"   🛡️  Table {table} préservée (Code SQL encore actif).")
                else:
                    print(f"   ℹ️  Table {table} absente (Sera recréée si nécessaire par SQLAlchemy).")

            # --- ÉTAPE 3 : CRÉER FEED_ITEMS (SI MANQUANTE) ---
            print("\n3️⃣  Vérification de 'feed_items'...")
            if 'feed_items' not in existing_tables:
                print("   ➕ Création de 'feed_items'...")
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
                print("   ✅ Table créée.")
            else:
                print("   ✅ Table 'feed_items' déjà présente.")

            trans.commit()
            print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS !")
            print("   Votre base est prête pour le profil JSON sans perte de données.")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ ERREUR MIGRATION : {e}")
            raise e

if __name__ == "__main__":
    run_migration()