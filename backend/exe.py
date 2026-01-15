import sys
import os
import logging
from sqlalchemy import create_engine, text, inspect

# 1. Configuration du Path pour trouver le module 'app'
# On s'assure que le script peut importer les fichiers du backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.database import engine, Base
    # IMPORTANT : On importe les modèles pour qu'ils soient enregistrés dans Base.metadata
    from app.models import sql_models
except ImportError as e:
    print("❌ Erreur d'import : Assurez-vous d'être dans le dossier 'backend' et que l'environnement virtuel est activé.")
    print(f"Détail : {e}")
    sys.exit(1)

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TitanDBUpdater")

def update_database():
    """
    Met à jour le schéma de la base de données.
    Utilise create_all() qui est 'SAFE' : il ne crée que ce qui manque.
    Il ne supprime rien, il ne modifie pas les colonnes existantes.
    """
    print("🚀 DÉMARRAGE DE LA MISE À JOUR BDD (ENGRAMMES)...")
    
    try:
        # 1. Inspection préalable
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"📊 Tables actuelles : {', '.join(existing_tables)}")
        
        if 'coach_engrams' in existing_tables:
            print("ℹ️  La table 'coach_engrams' existe déjà.")
        else:
            print("🆕 La table 'coach_engrams' est manquante. Elle sera créée.")

        # 2. Application des changements
        # C'est ici que la magie opère : SQLAlchemy regarde sql_models.py et crée les tables manquantes
        Base.metadata.create_all(bind=engine)
        
        # 3. Vérification post-update
        inspector = inspect(engine)
        new_tables = inspector.get_table_names()
        
        if 'coach_engrams' in new_tables:
            print("\n✅ SUCCÈS : La table 'coach_engrams' est opérationnelle !")
            
            # Vérification des colonnes pour être sûr
            columns = [col['name'] for col in inspector.get_columns('coach_engrams')]
            print(f"   Structure validée : {columns}")
        else:
            print("\n❌ ERREUR : La table n'a pas été créée. Vérifiez les logs.")

    except Exception as e:
        print(f"\n🔥 CRASH : Une erreur est survenue lors de la mise à jour.")
        print(f"Détail : {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_database()