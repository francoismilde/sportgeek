import os

# Détection automatique du chemin
POSSIBLE_PATHS = [
    os.path.join("backend", "app", "main.py"),
    os.path.join("app", "main.py"),
]

def fix_import():
    main_path = next((p for p in POSSIBLE_PATHS if os.path.exists(p)), None)
    
    if not main_path:
        print("❌ Impossible de trouver main.py")
        return

    print(f"🔧 Réparation des imports dans : {main_path}")

    with open(main_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Vérification si l'import existe déjà sous une autre forme
    content = "".join(lines)
    if "import profiles" in content and "from" in content:
        print("⚠️ L'import semble déjà présent. Vérification manuelle requise si le crash persiste.")
        # On continue quand même pour forcer l'import explicite si besoin

    # On cherche la section des imports pour insérer le nôtre
    # On va l'insérer juste avant "app = FastAPI(...)" ou après les derniers imports
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith("from") or line.startswith("import"):
            insert_index = i
    
    # On ajoute l'import explicite juste après le dernier import trouvé
    # C'est la méthode "Brute Force" mais sûre : on importe directement le module
    new_import = "from app.routers import profiles\n"
    
    # On vérifie qu'on ne l'ajoute pas en double
    if new_import not in lines:
        lines.insert(insert_index + 1, new_import)
        print("   ➕ Ajout de : from app.routers import profiles")
    else:
        print("   ℹ️ L'import était déjà là (bizarre).")

    with open(main_path, "w", encoding="utf-8") as f:
        f.write("".join(lines))
        
    print("✅ Réparation terminée.")

if __name__ == "__main__":
    fix_import()