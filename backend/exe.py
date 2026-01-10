# fix_coachmemory_schema.py
import os
import re

# Chemin vers le fichier problématique
SCHEMA_PATH = "backend/app/models/schemas.py"

# Lecture du fichier
with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Recherche de la classe CoachMemoryResponse
pattern = r'class CoachMemoryResponse\(BaseModel\):.*?^\}'
match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

if match:
    coach_memory_response = match.group(0)
    
    # Correction de la ligne problématique
    # Remplacer la ligne incorrecte par la version correcte
    corrected_line = '    readiness_score: int = Field(default=0, alias="current_context")'
    
    # Remplacer la ligne dans le contenu
    lines = content.split('\n')
    in_coach_memory = False
    for i, line in enumerate(lines):
        if 'class CoachMemoryResponse' in line:
            in_coach_memory = True
        elif in_coach_memory and 'readiness_score:' in line and 'Field(' in line:
            # Trouvée ! On la remplace
            lines[i] = corrected_line
            print(f"✅ Ligne {i+1} corrigée : {line} -> {corrected_line}")
            break
    
    # Écrire le fichier corrigé
    with open(SCHEMA_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Fichier schemas.py corrigé avec succès !")
    
else:
    # Si le pattern n'est pas trouvé, essayons une autre approche
    print("⚠️  Pattern non trouvé, tentative de correction directe...")
    
    # Recherche directe de la ligne problématique
    content = re.sub(
        r'readiness_score: int = Field\(alias="current_context", default=\{\}\)\.get\("readiness_score", 0\)',
        '    readiness_score: int = Field(default=0, alias="current_context")',
        content
    )
    
    with open(SCHEMA_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Correction appliquée (approche alternative) !")

# Vérifions aussi le deuxième fichier schemas.py s'il existe
SECOND_SCHEMA_PATH = "backend/backend/app/models/schemas.py"
if os.path.exists(SECOND_SCHEMA_PATH):
    print(f"🔍 Vérification du deuxième fichier: {SECOND_SCHEMA_PATH}")
    
    with open(SECOND_SCHEMA_PATH, 'r', encoding='utf-8') as f:
        content2 = f.read()
    
    # Vérifier s'il contient la même erreur
    if 'Field(alias="current_context", default={}).get("readiness_score"' in content2:
        print("⚠️  Deuxième fichier contient aussi l'erreur, correction...")
        content2 = re.sub(
            r'readiness_score: int = Field\(alias="current_context", default=\{\}\)\.get\("readiness_score", 0\)',
            '    readiness_score: int = Field(default=0, alias="current_context")',
            content2
        )
        
        with open(SECOND_SCHEMA_PATH, 'w', encoding='utf-8') as f:
            f.write(content2)
        
        print("✅ Deuxième fichier corrigé !")
    else:
        print("✅ Deuxième fichier est déjà correct.")

print("\n🚀 Correction terminée ! Redémarrez le serveur.")