import os

# Liste des fichiers qui utilisent ce service et doivent être corrigés
files_to_fix = [
    os.path.join("backend", "app", "routers", "athlete_profiles.py"),
    os.path.join("backend", "app", "routers", "coach_memories.py"),
    os.path.join("app", "routers", "athlete_profiles.py"),
    os.path.join("app", "routers", "coach_memories.py")
]

# Le mauvais import (celui qui plante)
bad_import = "from app.services.coach_memory_service import"

# Le bon import (celui qui correspond à votre structure de fichiers)
good_import = "from app.services.coach_memory.service import"

print("🔧 Réparation des imports de services...")

fixed_count = 0

for file_path in files_to_fix:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if bad_import in content:
                print(f"⚠️  Erreur trouvée dans : {file_path}")
                
                # Remplacement
                new_content = content.replace(bad_import, good_import)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                    
                print(f"✅  Corrigé : {file_path}")
                fixed_count += 1
            else:
                print(f"ℹ️  Fichier sain ou introuvable : {file_path}")
                
        except Exception as e:
            print(f"❌ Erreur lecture {file_path}: {e}")

if fixed_count > 0:
    print(f"\n🎉 Terminé ! {fixed_count} fichiers ont été réparés.")
else:
    print("\n🤔 Aucune erreur trouvée. Vérifiez que vous êtes à la racine du projet.")
    # Fallback : Si le fichier service.py est mal placé, on peut créer un alias
    service_path = os.path.join("backend", "app", "services", "coach_memory", "service.py")
    if os.path.exists(service_path):
        print(f"ℹ️  Le service existe bien ici : {service_path}")
        print("    L'import correct est : from app.services.coach_memory.service import ...")