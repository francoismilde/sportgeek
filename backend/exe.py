import os

# Liste des chemins possibles pour main.py
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

print(f"🔧 Réparation finale de : {target_file}")

with open(target_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
import_fixed = False

# On parcourt le fichier ligne par ligne
for line in lines:
    # On repère la ligne des imports de routeurs
    if "from app.routers import" in line:
        if not import_fixed:
            # On remplace cette ligne (et potentiellement les suivantes si c'était multiligne)
            # par une ligne unique et complète qui inclut TOUT.
            print("📝 Remplacement de la ligne d'import...")
            new_lines.append("from app.routers import performance, safety, auth, workouts, coach, user, feed, profiles, athlete_profiles, coach_memories\n")
            import_fixed = True
        else:
            # Si on a déjà mis notre ligne fixée, on ignore les autres lignes d'imports de routeurs
            # (cas où l'ancien script aurait mis des doublons)
            continue
    else:
        new_lines.append(line)

# Sécurité : Si on n'a pas trouvé la ligne, on l'ajoute après les imports système
if not import_fixed:
    print("⚠️ Ligne d'import introuvable, insertion forcée en tête.")
    final_lines = []
    inserted = False
    for line in new_lines:
        final_lines.append(line)
        if "from sqlalchemy" in line and not inserted:
             final_lines.append("from app.routers import performance, safety, auth, workouts, coach, user, feed, profiles, athlete_profiles, coach_memories\n")
             inserted = True
    new_lines = final_lines

# Écriture du fichier corrigé
with open(target_file, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("✅ main.py a été réécrit avec les imports complets.")