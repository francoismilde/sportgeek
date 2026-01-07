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
        # Ajout de energy_level
        connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS energy_level INTEGER DEFAULT 5;"))
        # Ajout de notes
        connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS notes TEXT;"))
        print("✅ Table 'workout_sessions' vérifiée (energy_level, notes).")
        
        # --- MIGRATION USERS ---
        # Ajout de profile_data pour la sauvegarde du profil
        connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"))
        print("✅ Table 'users' vérifiée (profile_data).")
        
        trans.commit()
        print("🎉 Migration terminée avec succès ! Tes tables sont à jour Coach.")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Erreur lors de la migration : {e}")