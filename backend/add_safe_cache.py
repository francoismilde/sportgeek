import re

with open('app/routers/coach.py', 'r') as f:
    content = f.read()

# Trouver generate_workout et ajouter un décorateur safe
func_pattern = r'async def generate_workout\([\s\S]*?\):'
match = re.search(func_pattern, content)

if match:
    func_start = match.start()
    
    # Ajouter le décorateur safe (ignore current_user)
    decorated_func = '@cached_response_fixed(ttl_hours=6, ignore_args=["current_user"])\n' + match.group(0)
    
    new_content = content[:func_start] + decorated_func + content[func_start + len(match.group(0)):]
    
    with open('app/routers/coach.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Décorateur safe ajouté à generate_workout")
else:
    print("⚠️  Impossible de trouver generate_workout")
