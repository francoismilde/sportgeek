#!/usr/bin/env python3
"""
SCRIPT DE MIGRATION CHIRURGICALE TITAN V2
Objectif : Passer au Profil JSON sans perdre les utilisateurs.
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
    print("🚀 DÉMARRAGE DE LA MIGRATION CHIRURGICALE...")
    
    engine = create_engine(get_db_url())
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            # --- ÉTAPE 1 : AJOUTER LA COLONNE JSON À USERS ---
            print("\n1️⃣  Vérification de la table 'users'...")
            if 'users' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('users')]
                
                if 'profile_data' not in columns:
                    print("   ➕ Ajout de la colonne 'profile_data'...")
                    # Syntaxe compatible Postgres (JSONB) et SQLite (TEXT/JSON)
                    is_postgres = "postgres" in str(engine.url)
                    col_type = "JSONB" if is_postgres else "JSON"
                    
                    if not is_postgres: col_type = "TEXT" # Fallback SQLite

                    conn.execute(text(f"ALTER TABLE users ADD COLUMN profile_data {col_type} DEFAULT '{{}}'"))
                    print("   ✅ Colonne ajoutée avec succès.")
                else:
                    print("   ✅ Colonne 'profile_data' déjà présente.")
            else:
                print("   ⚠️ Table 'users' introuvable (sera créée au redémarrage).")

            # --- ÉTAPE 2 : SUPPRIMER LES TABLES CONFLICTUELLES ---
            print("\n2️⃣  Nettoyage des anciennes tables...")
            tables_to_drop = ['coach_memories', 'athlete_profiles']
            
            for table in tables_to_drop:
                if table in existing_tables:
                    print(f"   🗑️  Suppression de {table}...")
                    conn.execute(text(f"DROP TABLE {table} CASCADE"))
                    print("   ✅ Supprimée.")
                else:
                    print(f"   ✨ {table} déjà propre.")

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
            print("   Vos utilisateurs sont saufs et le schéma est à jour.")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ ERREUR MIGRATION : {e}")
            raise e

if __name__ == "__main__":
    run_migration()