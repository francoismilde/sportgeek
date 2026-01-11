#!/usr/bin/env python3
"""
Script autonome de migration de base de données pour TitanFlow
Exécute toutes les migrations nécessaires pour les tables Feed & Workouts
"""

import sys
import os
from pathlib import Path

# Ajouter le backend au path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def check_database_status():
    """Vérifie l'état actuel de la base de données"""
    print("🔍 Diagnostic de la base de données...")
    
    db_url = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📊 {len(tables)} tables trouvées:")
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            print(f"  - {table}: {len(columns)} colonnes")
            for col in columns[:3]:  # Afficher seulement 3 colonnes par table
                print(f"    • {col['name']} ({col['type']})")
    
    return engine

def create_feed_items_table(engine):
    """Crée la table feed_items si elle n'existe pas"""
    print("\n📨 Création de la table feed_items...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Vérifier si la table existe déjà
            inspector = inspect(engine)
            if 'feed_items' in inspector.get_table_names():
                print("✅ Table feed_items existe déjà")
                return
            
            # Créer la table
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
            
            # Créer les index
            conn.execute(text("""
                CREATE INDEX idx_feed_items_user_id 
                ON feed_items(user_id) WHERE is_completed = FALSE;
            """))
            
            conn.execute(text("""
                CREATE INDEX idx_feed_items_type 
                ON feed_items(type);
            """))
            
            conn.execute(text("""
                CREATE INDEX idx_feed_items_priority_created 
                ON feed_items(priority DESC, created_at DESC);
            """))
            
            trans.commit()
            print("✅ Table feed_items créée avec succès")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Erreur création feed_items: {e}")
            raise

def add_missing_columns(engine):
    """Ajoute les colonnes manquantes aux tables existantes"""
    print("\n➕ Ajout des colonnes manquantes...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            inspector = inspect(engine)
            
            # Table WORKOUT_SESSIONS
            if 'workout_sessions' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('workout_sessions')]
                
                if 'energy_level' not in columns:
                    conn.execute(text("ALTER TABLE workout_sessions ADD COLUMN energy_level INTEGER DEFAULT 5;"))
                    print("✅ Colonne energy_level ajoutée à workout_sessions")
                
                if 'notes' not in columns:
                    conn.execute(text("ALTER TABLE workout_sessions ADD COLUMN notes TEXT;"))
                    print("✅ Colonne notes ajoutée à workout_sessions")
                
                if 'ai_analysis' not in columns:
                    conn.execute(text("ALTER TABLE workout_sessions ADD COLUMN ai_analysis TEXT;"))
                    print("✅ Colonne ai_analysis ajoutée à workout_sessions")
                
                if 'created_at' not in columns:
                    conn.execute(text("ALTER TABLE workout_sessions ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();"))
                    print("✅ Colonne created_at ajoutée à workout_sessions")
            
            # Table WORKOUT_SETS
            if 'workout_sets' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('workout_sets')]
                
                if 'rest_seconds' not in columns:
                    conn.execute(text("ALTER TABLE workout_sets ADD COLUMN rest_seconds INTEGER DEFAULT 0;"))
                    print("✅ Colonne rest_seconds ajoutée à workout_sets")
                
                if 'metric_type' not in columns:
                    conn.execute(text("ALTER TABLE workout_sets ADD COLUMN metric_type VARCHAR DEFAULT 'LOAD_REPS';"))
                    print("✅ Colonne metric_type ajoutée à workout_sets")
            
            trans.commit()
            print("✅ Toutes les colonnes manquantes ont été ajoutées")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Erreur ajout colonnes: {e}")
            raise

def add_constraints(engine):
    """Ajoute les contraintes de validation"""
    print("\n🔒 Ajout des contraintes de validation...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Contrainte feed_items.priority
            conn.execute(text("""
                ALTER TABLE feed_items 
                ADD CONSTRAINT IF NOT EXISTS check_feed_item_priority 
                CHECK (priority BETWEEN 1 AND 10);
            """))
            print("✅ Contrainte check_feed_item_priority ajoutée")
            
            # Contraintes workout_sessions
            conn.execute(text("""
                ALTER TABLE workout_sessions 
                ADD CONSTRAINT IF NOT EXISTS check_rpe_range 
                CHECK (rpe BETWEEN 0 AND 10);
            """))
            print("✅ Contrainte check_rpe_range ajoutée")
            
            conn.execute(text("""
                ALTER TABLE workout_sessions 
                ADD CONSTRAINT IF NOT EXISTS check_energy_range 
                CHECK (energy_level BETWEEN 1 AND 10);
            """))
            print("✅ Contrainte check_energy_range ajoutée")
            
            trans.commit()
            print("✅ Toutes les contraintes ont été ajoutées")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Erreur ajout contraintes: {e}")

def verify_migration(engine):
    """Vérifie que la migration a réussi"""
    print("\n🧪 Vérification de la migration...")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # Vérifier les tables critiques
    critical_tables = ['feed_items', 'workout_sessions', 'workout_sets', 'users']
    missing_tables = [t for t in critical_tables if t not in tables]
    
    if missing_tables:
        print(f"❌ Tables manquantes: {missing_tables}")
        return False
    
    # Vérifier les colonnes critiques
    critical_columns = {
        'workout_sessions': ['ai_analysis', 'energy_level'],
        'workout_sets': ['metric_type', 'rest_seconds'],
        'feed_items': ['type', 'title', 'message', 'priority']
    }
    
    for table, columns in critical_columns.items():
        if table in tables:
            table_columns = [col['name'] for col in inspector.get_columns(table)]
            missing = [col for col in columns if col not in table_columns]
            if missing:
                print(f"❌ Colonnes manquantes dans {table}: {missing}")
                return False
    
    print("✅ Migration vérifiée avec succès !")
    return True

def main():
    """Fonction principale"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║       MIGRATION BASE DE DONNÉES TITANFLOW        ║
    ║            🗃️  Feed & Workouts Schema           ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    try:
        # 1. Vérifier l'état actuel
        engine = check_database_status()
        
        # 2. Créer la table feed_items
        create_feed_items_table(engine)
        
        # 3. Ajouter les colonnes manquantes
        add_missing_columns(engine)
        
        # 4. Ajouter les contraintes
        add_constraints(engine)
        
        # 5. Vérifier la migration
        success = verify_migration(engine)
        
        if success:
            print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS !")
            print("\n📋 RÉSUMÉ:")
            print("   - ✅ Table feed_items créée")
            print("   - ✅ Colonnes ai_analysis, energy_level ajoutées")
            print("   - ✅ Colonnes metric_type, rest_seconds ajoutées")
            print("   - ✅ Index de performance créés")
            print("   - ✅ Contraintes de validation ajoutées")
            print("\n🚀 POUR TESTER:")
            print("   - Accédez à /health pour vérifier l'état du backend")
            print("   - Accédez à /fix_db pour forcer la migration via API")
            print("   - Testez les endpoints: GET /feed/, POST /workouts/")
        else:
            print("\n❌ MIGRATION ÉCHOUÉE")
            print("   Vérifiez les logs ci-dessus")
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()