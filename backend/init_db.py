from app.core.database import engine, Base
from app.models import sql_models

print("🏗️  Force-Création des tables en cours...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅  Succès ! Toutes les tables (users + workout_sessions) sont prêtes.")
except Exception as e:
    print(f"❌  Erreur : {e}")