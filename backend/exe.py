import os

# Le code manquant à injecter
MISSING_CODE = """
# --- AUTO-INJECTED UPDATE SCHEMAS ---

class AthleteProfileUpdate(AthleteProfileBase):
    pass

class ProfileSectionUpdate(BaseModel):
    section_data: Dict[str, Any]

class DailyMetrics(BaseModel):
    date: str
    weight: Optional[float] = None
    sleep_quality: Optional[int] = None
    resting_heart_rate: Optional[int] = None
    hrv: Optional[int] = None
    energy_level: Optional[int] = None
    muscle_soreness: Optional[int] = None
    perceived_stress: Optional[int] = None
    sleep_duration: Optional[float] = None

class GoalProgressUpdate(BaseModel):
    progress_value: int
    progress_note: Optional[str] = None
    achieved: bool = False
"""

print("🚀 Recherche de tous les fichiers schemas.py...")

found_count = 0
fixed_count = 0

# On parcourt tout le projet récursivement
for root, dirs, files in os.walk("."):
    for file in files:
        if file == "schemas.py":
            file_path = os.path.join(root, file)
            found_count += 1
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Vérifie si le fichier est un fichier de modèles (contient BaseModel)
                if "class BaseModel" in content or "from pydantic import BaseModel" in content:
                    
                    # Vérifie si la classe manque
                    if "class AthleteProfileUpdate" not in content:
                        print(f"🔧 Réparation de : {file_path}")
                        
                        # On ajoute le code à la fin
                        with open(file_path, "a", encoding="utf-8") as f:
                            f.write("\n" + MISSING_CODE)
                        
                        fixed_count += 1
                    else:
                        print(f"✅ Déjà complet : {file_path}")
                else:
                    print(f"ℹ️ Ignoré (pas un fichier Pydantic) : {file_path}")
                    
            except Exception as e:
                print(f"❌ Erreur sur {file_path}: {e}")

print("-" * 30)
if fixed_count > 0:
    print(f"🎉 Succès ! {fixed_count} fichier(s) schemas.py ont été mis à jour.")
else:
    print("🤔 Aucun fichier n'avait besoin de modification (ou schemas.py introuvable).")