import sys
import os
import json
import inspect
import re

# --- CONFIGURATION DES CHEMINS ---
# On se place dans backend/tools/, on veut remonter à la racine du projet
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
PUBSPEC_PATH = os.path.join(BASE_DIR, 'pubspec.yaml') # Hypothèse: pubspec à la racine ou dans frontend/
REQUIREMENTS_PATH = os.path.join(BACKEND_DIR, 'requirements.txt')
MAP_FILE = os.path.join(BASE_DIR, 'TITANFLOW_MAP.json')

# Ajout du backend au path pour les imports SQLAlchemy
sys.path.append(BACKEND_DIR)

try:
    from app.models import sql_models
    from app.core.database import Base
except ImportError as e:
    print(f"❌ Erreur d'import Backend : {e}")
    print("Assurez-vous d'être dans l'environnement virtuel (venv).")
    sys.exit(1)

def get_flutter_environment():
    """Lit le pubspec.yaml pour extraire les versions."""
    env = {"sdk": "Unknown", "packages": {}}
    
    if not os.path.exists(PUBSPEC_PATH):
        print(f"⚠️  pubspec.yaml introuvable ici : {PUBSPEC_PATH}")
        return env

    with open(PUBSPEC_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    in_dependencies = False
    for line in lines:
        line = line.strip()
        # SDK Version
        if line.startswith('sdk:'):
            env['sdk'] = line.split(':')[1].strip()
        
        # Détection bloc dependencies
        if line == 'dependencies:':
            in_dependencies = True
            continue
        if line == 'dev_dependencies:':
            in_dependencies = False
            continue
            
        # Extraction packages clés (http, provider, etc.)
        if in_dependencies and ':' in line:
            parts = line.split(':')
            pkg_name = parts[0].strip()
            version = parts[1].strip()
            # On garde seulement les packages intéressants pour l'IA
            interesting_libs = ['http', 'shared_preferences', 'intl', 'flutter', 'provider', 'riverpod', 'bloc', 'go_router']
            if pkg_name in interesting_libs:
                env['packages'][pkg_name] = version
                
    return env

def get_backend_environment():
    """Lit le requirements.txt pour les versions Python."""
    env = {"python": sys.version.split()[0], "libs": {}}
    
    if not os.path.exists(REQUIREMENTS_PATH):
        return env

    with open(REQUIREMENTS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '==' in line:
                parts = line.split('==')
                env['libs'][parts[0]] = parts[1]
            elif '>=' in line:
                parts = line.split('>=')
                env['libs'][parts[0]] = f">={parts[1]}"
                
    return env

def generate_db_schema():
    """Scan les modèles SQLAlchemy."""
    schema = {}
    for name, obj in inspect.getmembers(sql_models):
        if inspect.isclass(obj) and issubclass(obj, Base) and obj != Base:
            table_name = obj.__tablename__
            columns = []
            
            for col in obj.__table__.columns:
                col_type = str(col.type)
                info = f"{col.name} ({col_type})"
                if col.primary_key: info += " [PK]"
                if col.foreign_keys: info += " [FK]"
                columns.append(info)
            
            schema[table_name] = {
                "description": f"Table SQL {table_name}",
                "columns": columns
            }
    return schema

def main():
    print("🚀 Démarrage de la cartographie TitanFlow...")
    
    # 1. Chargement existant
    data = {}
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("⚠️  Fichier JSON corrompu, création d'un nouveau.")

    # 2. Mise à jour Environment (Versions)
    print("📦 Analyse des dépendances (Flutter & Python)...")
    data["environment"] = {
        "frontend": get_flutter_environment(),
        "backend": get_backend_environment()
    }

    # 3. Mise à jour DB Schema
    print("🗄️  Introspection de la Base de Données...")
    data["database_schema"] = generate_db_schema()

    # 4. Sauvegarde
    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Succès ! Fichier mis à jour : {MAP_FILE}")
    print("   -> L'IA aura maintenant une vision exacte de tes versions et de ta BDD.")

if __name__ == "__main__":
    main()