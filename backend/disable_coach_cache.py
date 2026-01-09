import re

with open('app/routers/coach.py', 'r') as f:
    content = f.read()

# Supprimer TOUTES les références à cache dans ce fichier
content = re.sub(r'from app\.core\.cache import[^\n]*\n', '', content)
content = re.sub(r'@cached_response[^\n]*\n', '', content)

with open('app/routers/coach.py', 'w') as f:
    f.write(new_content)

print("✅ Cache complètement désactivé pour coach.py")
