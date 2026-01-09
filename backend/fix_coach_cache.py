#!/usr/bin/env python3
"""
Retire le décorateur @cached_response de la fonction generate_workout
qui cause l'erreur de sérialisation JSON
"""

import re

with open('app/routers/coach.py', 'r') as f:
    content = f.read()

# Trouver la fonction generate_workout
pattern = r'@cached_response\(ttl_hours=6\)\s*\nasync def generate_workout'
match = re.search(pattern, content)

if match:
    print("🔧 Retrait du décorateur @cached_response problématique...")
    
    # Retirer la ligne du décorateur
    new_content = content.replace(match.group(0), 'async def generate_workout')
    
    with open('app/routers/coach.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Décorateur retiré avec succès")
else:
    print("✅ Le décorateur n'est pas présent ou a déjà été retiré")
