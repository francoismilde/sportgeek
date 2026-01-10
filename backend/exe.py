import os

file_path = os.path.join("backend", "migrate_db.py")
if not os.path.exists(file_path):
    file_path = "migrate_db.py"

if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # On cherche le bloc incomplet
    old_block = '("profile_data", "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"),'
    
    # On ajoute la ligne email juste avant si elle n\'y est pas
    new_line = '                    ("email", "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;"),\n'
    
    if '("email",' not in content and old_block in content:
        new_content = content.replace(old_block, new_line + "                    " + old_block)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ migrate_db.py a été mis à jour avec la colonne email !")
    else:
        print("ℹ️ Le fichier semble déjà à jour ou le motif n'a pas été trouvé.")
else:
    print("❌ Fichier migrate_db.py introuvable.")