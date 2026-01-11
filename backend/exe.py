#!/usr/bin/env python3
"""
HOTFIX TITANFLOW
Ajoute les schémas manquants (AthleteProfileUpdate, ProfileSectionUpdate)
qui causent le crash au démarrage.
"""

import os
from pathlib import Path

# Chemin vers schemas.py
BASE_DIR = Path(__file__).parent
SCHEMAS_FILE = BASE_DIR / "app" / "models" / "schemas.py"

MISSING_CODE = """

# --- HOTFIX: MISSING SCHEMAS ADDED ---

class AthleteProfileUpdate(AthleteProfileBase):
    pass

class ProfileSectionUpdate(BaseModel):
    section_data: Dict[str, Any]

"""

def fix_schemas():
    print(f"🔧 Vérification de {SCHEMAS_FILE}...")
    
    if not SCHEMAS_FILE.exists():
        # Fallback si le script est lancé depuis la racine du projet
        alt_path = Path("backend") / "app" / "models" / "schemas.py"
        if alt_path.exists():
            target_file = alt_path
        else:
            print("❌ Impossible de trouver schemas.py")
            return
    else:
        target_file = SCHEMAS_FILE

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Vérification et Patch
    if "class AthleteProfileUpdate" not in content:
        print("⚠️ AthleteProfileUpdate manquant. Application du patch...")
        
        with open(target_file, "a", encoding="utf-8") as f:
            f.write(MISSING_CODE)
            
        print("✅ Patch appliqué avec succès !")
    else:
        print("✅ AthleteProfileUpdate est déjà présent. Pas de modification nécessaire.")

if __name__ == "__main__":
    try:
        fix_schemas()
    except Exception as e:
        print(f"❌ Erreur critique : {e}")