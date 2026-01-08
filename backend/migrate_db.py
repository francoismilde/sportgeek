import os
import sqlalchemy
from sqlalchemy import text
from dotenv import load_dotenv

# Charge les variables locales si test local, sinon prend celles de Render
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Correction pour Render qui utilise parfois postgres:// au lieu de postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("❌ Erreur : Pas de DATABASE_URL trouvée.")
    exit(1)

print(f"🔌 Connexion à la BDD...")
engine = sqlalchemy.create_engine(DATABASE_URL)

with engine.connect() as connection:
    # 1. On active le mode Transaction
    trans = connection.begin()
    try:
        print("🛠️ Vérification des colonnes manquantes...")
        
        # --- MIGRATION WORKOUTS ---
        connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS energy_level INTEGER DEFAULT 5;"))
        connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS notes TEXT;"))
        connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();"))
        print("✅ Table 'workout_sessions' vérifiée.")

        # --- MIGRATION SETS ---
        connection.execute(text("ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS metric_type VARCHAR DEFAULT 'LOAD_REPS';"))
        connection.execute(text("ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS rest_seconds INTEGER DEFAULT 0;"))
        print("✅ Table 'workout_sets' vérifiée.")
        
        # --- MIGRATION USERS ---
        # Ajout de profile_data pour la sauvegarde du profil
        connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"))
        
        # Ajout des colonnes IA (Stratégie & Planning)
        connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS strategy_data TEXT;"))
        connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_plan_data TEXT;"))
        
        # [FIX] Ajout de la colonne Brouillon (Draft) qui causait le crash
        connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS draft_workout_data TEXT;"))
        
        print("✅ Table 'users' vérifiée (profile, strategy, weekly, draft).")
        
        # --- [DEV-CARD #01] MIGRATION FEED ---
        # On crée la table feed_items si elle n'existe pas
        # Note : On utilise UUID en String pour l'ID
        create_feed_table_sql = """
        CREATE TABLE IF NOT EXISTS feed_items (
            id VARCHAR PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            type VARCHAR,
            title VARCHAR,
            message VARCHAR,
            action_payload TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            is_completed BOOLEAN DEFAULT FALSE,
            priority INTEGER DEFAULT 1,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        connection.execute(text(create_feed_table_sql))
        print("✅ Table 'feed_items' vérifiée/créée.")

        trans.commit()
        print("🎉 Migration terminée avec succès ! Tes tables sont à jour Coach.")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Erreur lors de la migration : {e}")