import os

# Liste des endroits probables où peut se cacher main.py
POSSIBLE_PATHS = [
    os.path.join("backend", "app", "main.py"),      # Si tu es à la racine
    os.path.join("app", "main.py"),                 # Si tu es dans le dossier backend
    os.path.join("backend", "backend", "app", "main.py"), # Cas rare de structure imbriquée
]

def find_main_py():
    """Cherche le fichier main.py dans les chemins connus"""
    for path in POSSIBLE_PATHS:
        if os.path.exists(path):
            return path
    return None

def fix_routing():
    print("🕵️‍♂️ Recherche du fichier main.py...")
    main_path = find_main_py()
    
    if not main_path:
        print("❌ ERREUR : Impossible de trouver main.py.")
        print(f"   J'ai cherché ici : {POSSIBLE_PATHS}")
        print("   Conseil : Place ce script à la racine du projet (là où il y a le dossier 'backend').")
        return

    print(f"✅ Fichier trouvé : {main_path}")
    print("🔧 Application du correctif de routage...")

    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Ajouter l'import de profiles si absent
    if "from .routers import" in content and "profiles" not in content:
        content = content.replace(
            "from .routers import",
            "from .routers import profiles, " 
        )
        print("   ➕ Import 'profiles' ajouté.")

    # 2. Désactiver l'ancien routeur (user.py sur /api/v1/profiles)
    # C'est lui le COUPABLE du 422
    old_route_block = 'app.include_router(\n    user.router, \n    prefix="/api/v1/profiles", \n    tags=["Profiles"]\n)'
    old_route_line = 'app.include_router(user.router, prefix="/api/v1/profiles", tags=["Profiles"])'
    
    if old_route_block in content:
        content = content.replace(old_route_block, '# 🚫 CONFLIT DÉSACTIVÉ\n# ' + old_route_block.replace('\n', '\n# '))
        print("   🚫 Ancien routeur (user.py) désactivé.")
    elif old_route_line in content:
        content = content.replace(old_route_line, '# 🚫 CONFLIT DÉSACTIVÉ\n# ' + old_route_line)
        print("   🚫 Ancien routeur (user.py) désactivé.")
    
    # 3. Activer le nouveau routeur (profiles.py)
    new_route = "app.include_router(profiles.router)"
    
    if new_route not in content:
        # On l'insère proprement après les autres routeurs
        insertion_point = "app.include_router(feed.router)"
        if insertion_point in content:
            content = content.replace(
                insertion_point,
                f"{insertion_point}\napp.include_router(profiles.router) # ✅ Nouveau routeur Profils"
            )
            print("   ✅ Nouveau routeur (profiles.py) activé.")
        else:
            # Fallback
            content += "\n\n# NOUVEAU ROUTEUR PROFILS\napp.include_router(profiles.router)"
            print("   ✅ Nouveau routeur ajouté à la fin.")

    # Sauvegarde
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("\n🎉 SUCCÈS : main.py a été corrigé.")
    print("👉 PROCHAINE ÉTAPE :")
    print("   git add .")
    print("   git commit -m 'fix: Resolve routing conflict 422'")
    print("   git push")

if __name__ == "__main__":
    fix_routing()