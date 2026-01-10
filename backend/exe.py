import os
import sys

# Récupère le dossier où se trouve ce script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_file(relative_variants):
    """Cherche un fichier parmi plusieurs chemins possibles"""
    for rel_path in relative_variants:
        full_path = os.path.join(BASE_DIR, rel_path)
        if os.path.exists(full_path):
            return full_path
    return None

# Détection automatique des chemins
SCHEMAS_PATH = find_file([
    "backend/app/models/schemas.py",  # Si lancé depuis la racine
    "app/models/schemas.py",          # Si lancé depuis backend/
    "models/schemas.py"               # Si lancé depuis app/
])

MAIN_PATH = find_file([
    "backend/app/main.py",            # Si lancé depuis la racine
    "app/main.py",                    # Si lancé depuis backend/
    "main.py"                         # Si lancé depuis app/
])

def fix_schemas():
    """Corrige l'AttributeError dans CoachMemoryResponse"""
    if not SCHEMAS_PATH:
        print("❌ Impossible de trouver schemas.py")
        return

    print(f"🔧 Réparation de {SCHEMAS_PATH}...")
    
    try:
        with open(SCHEMAS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        fixed = False
        for line in lines:
            # Recherche de la ligne cassée
            if 'readiness_score: int = Field(alias="current_context"' in line and '.get(' in line:
                # Remplacement par la syntaxe valide Pydantic
                new_lines.append('    readiness_score: int = Field(alias="current_context", default=50)\n')
                fixed = True
            else:
                new_lines.append(line)
        
        if fixed:
            with open(SCHEMAS_PATH, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print("✅ schemas.py réparé.")
        else:
            print("ℹ️ schemas.py semblait déjà correct (ou motif introuvable).")
            
    except Exception as e:
        print(f"❌ Erreur sur schemas.py: {e}")

def fix_main():
    """Corrige les imports en doublon dans main.py"""
    if not MAIN_PATH:
        print("❌ Impossible de trouver main.py")
        return

    print(f"🔧 Réparation de {MAIN_PATH}...")
    
    try:
        with open(MAIN_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 1. Correction de la ligne d'import corrompue
        bad_import = "from app.routers import performance, safety, auth, workouts, coach, user, feed, profiles, profiles, athlete_profiles, coach_memories"
        good_import = "from app.routers import performance, safety, auth, workouts, coach, user, feed, profiles"
        
        if bad_import in content:
            content = content.replace(bad_import, good_import)
            print("✅ Imports des routeurs corrigés.")
            
        # 2. Suppression des inclusions de routeurs en double
        if content.count("app.include_router(profiles.router)") > 1:
            parts = content.split("app.include_router(profiles.router)")
            # On garde la première partie + une inclusion + la dernière partie
            content = parts[0] + "app.include_router(profiles.router)" + parts[-1]
            print("✅ Doublons include_router supprimés.")

        with open(MAIN_PATH, "w", encoding="utf-8") as f:
            f.write(content)
            
    except Exception as e:
        print(f"❌ Erreur sur main.py: {e}")

if __name__ == "__main__":
    print(f"📂 Dossier de travail : {BASE_DIR}")
    fix_schemas()
    fix_main()
    print("\n🚀 Réparations terminées.")