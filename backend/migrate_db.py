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
        print("🛠️ Mise à jour de la table 'workout_sessions'...")
        # Ajout des colonnes manquantes si elles n'existent pas
        connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS energy_level INTEGER DEFAULT 5;"))
        connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS notes TEXT;"))
        
        print("✅ Table 'workout_sessions' mise à jour.")
        
        # 2. Pour la table 'workout_sets', SQLAlchemy la créera au démarrage s'il ne la trouve pas.
        # Mais on peut forcer le nettoyage si besoin.
        # Ici, on fait confiance à main.py pour le create_all() des nouvelles tables.
        
        trans.commit()
        print("🎉 Migration terminée avec succès !")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Erreur lors de la migration : {e}")