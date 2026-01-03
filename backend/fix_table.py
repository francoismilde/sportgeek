from sqlalchemy import text
from app.core.database import engine

print("☢️  Démarrage de l'option nucléaire...")

with engine.connect() as connection:
    # On force la transaction
    trans = connection.begin()
    try:
        # SQL Brut : On détruit la table et tout ce qui y est lié
        connection.execute(text("DROP TABLE IF EXISTS workout_sessions CASCADE;"))
        trans.commit()
        print("💥 Table workout_sessions pulvérisée avec succès.")
    except Exception as e:
        trans.rollback()
        print(f"❌ Erreur : {e}")

print("✅ Terminé. Le redémarrage du serveur recréera la table propre.")