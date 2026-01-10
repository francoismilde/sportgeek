import os

# On commence la recherche depuis le dossier actuel
ROOT_DIR = os.getcwd()

print(f"🚀 Recherche récursive de 'schemas.py' depuis : {ROOT_DIR}")

# La ligne toxique exacte (copiée depuis ton log d'erreur)
bad_pattern = 'readiness_score: int = Field(alias="current_context", default={}).get("readiness_score", 0)'

# La version corrigée
good_pattern = 'readiness_score: int = Field(alias="current_context", default=50)'

files_fixed = 0

for root, dirs, files in os.walk(ROOT_DIR):
    for file in files:
        if file == "schemas.py":
            full_path = os.path.join(root, file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Si on trouve la ligne toxique
                if bad_pattern in content:
                    print(f"⚠️  ERREUR TROUVÉE dans : {full_path}")
                    
                    # Correction
                    new_content = content.replace(bad_pattern, good_pattern)
                    
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
                    print(f"✅  Fichier corrigé avec succès !")
                    files_fixed += 1
                
                elif "CoachMemoryResponse" in content:
                    # Le fichier contient la classe mais pas l'erreur
                    print(f"ℹ️  Fichier sain (déjà corrigé) : {full_path}")
                    
            except Exception as e:
                print(f"❌ Impossible de lire {full_path}: {e}")

if files_fixed == 0:
    print("\n🤔 Aucun fichier corrompu trouvé.")
    print("Vérifie que tu lances ce script depuis la racine du projet (/opt/render/project/src ou équivalent).")
else:
    print(f"\n🎉 Terminé ! {files_fixed} fichier(s) caché(s) ont été corrigés.")