import os

# Chemins possibles pour main.py
possible_paths = [
    os.path.join("backend", "app", "main.py"),
    os.path.join("app", "main.py"),
    "main.py"
]

target_file = None
for path in possible_paths:
    if os.path.exists(path):
        target_file = path
        break

if not target_file:
    print("❌ Impossible de trouver main.py")
    exit(1)

print(f"🔧 Correction des imports dans : {target_file}")

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# 1. On cherche la ligne d'import des routeurs
# Elle ressemble généralement à : from app.routers import performance, safety...
if "from app.routers import" in content:
    # On vérifie si athlete_profiles est déjà importé
    if "athlete_profiles" not in content:
        print("⚠️  'athlete_profiles' manquant dans les imports.")
        
        # On remplace la ligne d'import pour ajouter les modules manquants
        # On cherche une ancre connue (le module 'user' ou 'feed')
        if "from app.routers import" in content:
            # On remplace toute la ligne d'import par la version complète
            # On utilise une Regex ou un replace simple si on connaît la structure
            
            # Approche simple : on ajoute une nouvelle ligne d'import explicite
            # C'est plus sûr que de tenter de modifier une ligne existante qui peut varier
            new_import = "from app.routers import athlete_profiles, coach_memories\n"
            
            # On l'insère juste après la ligne from app.routers import existante
            lines = content.splitlines()
            new_lines = []
            import_added = False
            
            for line in lines:
                new_lines.append(line)
                if "from app.routers import" in line and not import_added:
                    new_lines.append(new_import)
                    import_added = True
            
            new_content = "\n".join(new_lines)
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
                
            print("✅ Import ajouté : athlete_profiles et coach_memories")
    else:
        print("ℹ️  'athlete_profiles' semble déjà importé.")
else:
    print("❌ Impossible de localiser la zone d'imports dans main.py")

# Vérification finale
with open(target_file, "r", encoding="utf-8") as f:
    if "athlete_profiles" in f.read():
        print("🚀 Réparation validée.")
    else:
        print("⚠️  La réparation semble avoir échoué.")