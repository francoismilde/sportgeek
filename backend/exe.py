import sys
import os
from datetime import datetime, timedelta

# --- CONFIGURATION DU PATH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    # --- IMPORTS ---
    from app.core.database import Base, SQLALCHEMY_DATABASE_URL as DATABASE_URL
    # On importe TOUS les maillons de la chaîne
    from app.models.sql_models import CoachMemory, CoachEngram, User, AthleteProfile
    from app.models.enums import MemoryType, ImpactLevel, MemoryStatus

except ImportError as e:
    print(f"❌ Erreur d'import : {e}")
    sys.exit(1)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def repair_and_seed(target_user_id: int):
    db = SessionLocal()
    try:
        print(f"🔧 Démarrage du protocole de réparation pour User ID: {target_user_id}...")

        # ÉTAPE 1 : Validation de l'Utilisateur
        user = db.query(User).filter(User.id == target_user_id).first()
        if not user:
            print(f"❌ Erreur Fatale : L'utilisateur {target_user_id} n'existe pas dans la table 'users'.")
            return

        print(f"  - ✅ Utilisateur {target_user_id} trouvé.")

        # ÉTAPE 2 : Validation ou Création du Profil Athlétique
        profile = user.athlete_profile # Via la relation SQLAlchemy
        
        if not profile:
            print(f"  - ⚠️ Aucun profil athlétique trouvé pour cet user.")
            print(f"  - 🛠️ CRÉATION D'UN PROFIL D'URGENCE...")
            
            # Création d'un profil minimal pour satisfaire la Foreign Key
            profile = AthleteProfile(
                user_id=user.id,
                biometrics={"weight": 80, "height": 180}, # Valeurs par défaut
                performance_metrics={}
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            print(f"  - ✅ Profil créé avec succès ! Nouvel ID du profil : {profile.id}")
        else:
            print(f"  - ✅ Profil athlétique existant trouvé (ID: {profile.id}).")

        # C'est cet ID qu'on doit utiliser, pas forcément 17 !
        real_profile_id = profile.id

        # ÉTAPE 3 : Validation ou Création de la Mémoire
        memory = db.query(CoachMemory).filter(CoachMemory.athlete_profile_id == real_profile_id).first()
        
        if not memory:
            print(f"  - Création du conteneur CoachMemory pour le Profil {real_profile_id}...")
            memory = CoachMemory(
                athlete_profile_id=real_profile_id,
                coach_notes={},
                memory_flags={},
                current_context={}
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
        else:
            print(f"  - Conteneur CoachMemory trouvé (ID: {memory.id})")

        # ÉTAPE 4 : Injection des Engrammes (Souvenirs)
        engrams_data = [
            {
                "type": MemoryType.INJURY_REPORT,
                "impact": ImpactLevel.SEVERE,
                "status": MemoryStatus.ACTIVE,
                "content": "Douleur patellaire gauche (4/10). Stop Squat profond.",
                "tags": ["knee", "squat"],
                "start_date": datetime.now() - timedelta(days=2),
                "end_date": None
            },
            {
                "type": MemoryType.LIFE_CONSTRAINT,
                "impact": ImpactLevel.MODERATE,
                "status": MemoryStatus.SCHEDULED,
                "content": "Déplacement Londres. Matériel limité.",
                "tags": ["travel"],
                "start_date": datetime.now() + timedelta(days=5),
                "end_date": datetime.now() + timedelta(days=10)
            },
            {
                "type": MemoryType.STRATEGIC_OVERRIDE,
                "impact": ImpactLevel.MODERATE,
                "status": MemoryStatus.ACTIVE,
                "content": "Focus Hypertrophie Dos.",
                "tags": ["back", "hypertrophy"],
                "start_date": datetime.now() - timedelta(days=1),
                "end_date": datetime.now() + timedelta(days=30)
            }
        ]

        count = 0
        for data in engrams_data:
            exists = db.query(CoachEngram).filter(
                CoachEngram.memory_id == memory.id,
                CoachEngram.content == data["content"]
            ).first()
            
            if not exists:
                engram = CoachEngram(
                    memory_id=memory.id,
                    author="REPAIR_SCRIPT",
                    **data
                )
                db.add(engram)
                count += 1
        
        db.commit()
        print(f"✅ SUCCÈS TOTAL : {count} engrammes injectés pour l'Utilisateur {target_user_id} (Profil {real_profile_id}).")

    except Exception as e:
        print(f"❌ Erreur Critique : {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # On cible l'USER 17, le script se débrouillera pour trouver/créer le reste
    repair_and_seed(target_user_id=17)