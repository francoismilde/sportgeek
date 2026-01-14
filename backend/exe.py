from app.core.database import SessionLocal
from app.models.sql_models import AthleteProfile
import json

def check_performance_data():
    db = SessionLocal()
    try:
        # Remplacer 1 par l'ID de votre utilisateur de test
        profile = db.query(AthleteProfile).filter(
            AthleteProfile.user_id == 17
        ).first()
        
        if profile:
            print("✅ Profil trouvé pour user_id=1")
            print(f"📊 performance_baseline: {profile.performance_baseline}")
            print(f"📋 Type: {type(profile.performance_baseline)}")
            
            if profile.performance_baseline:
                print("\n🔍 Structure détaillée:")
                for key, value in profile.performance_baseline.items():
                    print(f"  - {key}: {value} (type: {type(value).__name__})")
                
                # Vérifier les champs spécifiques
                key_checks = ['running_vma', 'run_vma', 'cycling_ftp', 'ftp', 
                            'squat_1rm', 'bench_1rm', 'deadlift_1rm']
                print("\n🔎 Recherche des champs clés:")
                for key in key_checks:
                    if key in profile.performance_baseline:
                        print(f"  ✅ {key}: {profile.performance_baseline[key]}")
                    else:
                        print(f"  ❌ {key}: Non trouvé")
        else:
            print("❌ Aucun profil trouvé pour user_id=1")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_performance_data()