import re

with open('app/routers/coach.py', 'r') as f:
    content = f.read()

# Supprimer toutes les occurrences de @cached_response
new_content = re.sub(r'@cached_response\([^)]*\)\s*\n', '', content)

with open('app/routers/coach.py', 'w') as f:
    f.write(new_content)

print("✅ Tous les décorateurs @cached_response retirés")
