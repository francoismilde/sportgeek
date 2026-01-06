from sqlalchemy import text
from app.core.database import engine

print("☢️  Démarrage de l'option nucléaire...")

with engine.connect() as connection:
    trans = connection.begin()
    try:
        # On supprime d'abord les séances (qui dépendent des users)
        connection.execute(text("DROP TABLE IF EXISTS workout_sessions CASCADE;"))
        print("💥 Table workout_sessions pulvérisée.")
        
        # On supprime ensuite les users (pour recréer la table avec l'email)
        connection.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
        print("💥 Table users pulvérisée.")
        
        trans.commit()
    except Exception as e:
        trans.rollback()
        print(f"❌ Erreur : {e}")

print("✅ Terminé. Redémarre le serveur pour recréer les tables propres.")