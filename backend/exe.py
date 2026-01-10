import os

# Liste des chemins possibles pour schemas.py
possible_paths = [
    os.path.join("backend", "app", "models", "schemas.py"),
    os.path.join("app", "models", "schemas.py"),
    "schemas.py"
]

target_file = None
for path in possible_paths:
    if os.path.exists(path):
        target_file = path
        break

if not target_file:
    print("❌ Impossible de trouver schemas.py")
    exit(1)

print(f"🔧 Ajout des schémas manquants dans : {target_file}")

# Les schémas à ajouter
missing_code = """
# --- MISSING SCHEMAS FOR UPDATES ---

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

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# On vérifie si AthleteProfileUpdate existe déjà pour éviter les doublons
if "class AthleteProfileUpdate" not in content:
    with open(target_file, "a", encoding="utf-8") as f:
        f.write("\n" + missing_code)
    print("✅ Schémas ajoutés avec succès (AthleteProfileUpdate, DailyMetrics, etc.)")
else:
    print("ℹ️ Les schémas semblent déjà présents.")