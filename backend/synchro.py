import sys
import os
import json
import re
import datetime
from pathlib import Path
from typing import get_type_hints, List, Optional, Union, Any

# ==============================================================================
# 1. DÉTECTION INTELLIGENTE DES CHEMINS (AUTO-CONFIGURATION)
# ==============================================================================
print("🔍 Initialisation du scanner de projet...")

# On part de l'endroit où se trouve ce script
SCRIPT_PATH = Path(__file__).resolve()
CURRENT_DIR = SCRIPT_PATH.parent

# On remonte l'arborescence jusqu'à trouver le dossier qui contient 'backend' et 'frontend'
PROJECT_ROOT = None
search_dir = CURRENT_DIR

# On cherche sur 5 niveaux de profondeur max pour éviter de remonter à la racine système
for _ in range(5):
    if (search_dir / "backend").exists() and (search_dir / "frontend").exists():
        PROJECT_ROOT = search_dir
        break
    if search_dir.parent == search_dir: # On a atteint la racine système
        break
    search_dir = search_dir.parent

if PROJECT_ROOT is None:
    print("❌ ERREUR CRITIQUE : Impossible de trouver la racine du projet.")
    print("   Assurez-vous que ce script est bien DANS le dossier du projet (sportgeek).")
    print("   Structure attendue : un dossier contenant 'backend/' et 'frontend/'.")
    sys.exit(1)

BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_MODELS_DIR = PROJECT_ROOT / "frontend" / "lib" / "models" / "generated"

# Ajout du backend au Python Path pour les imports
sys.path.append(str(BACKEND_DIR))

print(f"✅ Racine détectée : {PROJECT_ROOT}")
print(f"📂 Source Backend : {BACKEND_DIR}")
print(f"📂 Cible Frontend : {FRONTEND_MODELS_DIR}")

# ==============================================================================
# 2. IMPORTATION DES MODÈLES (LE COEUR DU RÉACTEUR)
# ==============================================================================
try:
    from app.models.schemas import (
        # Auth & User
        UserResponse,
        Token,
        
        # Profil & Athlète
        AthleteProfileResponse,
        
        # Coach & Mémoire
        CoachMemoryResponse,
        CoachEngramResponse,
        
        # Workouts & Séances
        WorkoutSessionResponse,
        WorkoutSetResponse,
        
        # IA & Plans
        AIWorkoutPlan,
        AIExercise,
        WeeklyPlanResponse,
        StrategyResponse,
        ProfileAuditResponse,
        
        # Feed
        FeedItemResponse,
        
        # Performance & Safety
        OneRepMaxResponse,
        ACWRResponse
    )
    print("✅ Modèles Pydantic importés avec succès.")
except ImportError as e:
    print(f"\n❌ ERREUR D'IMPORT PYTHON : {e}")
    print("   Vérifiez que votre environnement virtuel est activé.")
    print("   (source venv/bin/activate)")
    sys.exit(1)

# Liste exhaustive des modèles à convertir
MODELS_TO_GENERATE = [
    UserResponse,
    Token,
    AthleteProfileResponse,
    CoachMemoryResponse,
    CoachEngramResponse,
    WorkoutSessionResponse,
    WorkoutSetResponse,
    AIWorkoutPlan,
    AIExercise,
    WeeklyPlanResponse,
    StrategyResponse,
    ProfileAuditResponse,
    FeedItemResponse,
    OneRepMaxResponse,
    ACWRResponse
]

# ==============================================================================
# 3. MOTEUR DE TRANSFORMATION (PYTHON -> DART)
# ==============================================================================

TYPE_MAP = {
    'str': 'String',
    'int': 'int',
    'float': 'double',
    'bool': 'bool',
    'datetime': 'DateTime',
    'date': 'DateTime',
    'dict': 'Map<String, dynamic>',
    'list': 'List',
    'any': 'dynamic',
    'nonetype': 'void'
}

def to_camel_case(snake_str):
    """Transforme snake_case en camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def get_dart_filename(class_name):
    """Nettoie le nom de la classe pour le fichier (ex: UserResponse -> user.dart)"""
    clean_name = class_name.replace("Response", "").replace("Schema", "")
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', clean_name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower() + ".dart"

def generate_dart_code(pydantic_model):
    """Génère le code source Dart pour un modèle donné"""
    
    # Nom de la classe Dart
    raw_name = pydantic_model.__name__
    dart_class_name = raw_name.replace("Response", "").replace("Schema", "")
    
    properties = []
    from_json_logic = []
    to_json_logic = []
    
    # Introspection du Schéma
    try:
        schema = pydantic_model.model_json_schema() # Pydantic V2
    except AttributeError:
        schema = pydantic_model.schema() # Pydantic V1
        
    props = schema.get('properties', {})
    
    for field_name, field_info in props.items():
        # --- ANALYSE DU TYPE ---
        py_type = field_info.get('type', 'any')
        dart_type = "dynamic"
        
        # Gestion des références ($ref) vers d'autres objets
        ref_obj = None
        if '$ref' in field_info:
            ref_obj = field_info['$ref'].split('/')[-1]
        elif 'anyOf' in field_info:
            for opt in field_info['anyOf']:
                if '$ref' in opt:
                    ref_obj = opt['$ref'].split('/')[-1]
                    break
        
        is_complex = False
        is_list_complex = False
        
        if ref_obj:
            dart_type = ref_obj.replace("Response", "").replace("Schema", "")
            is_complex = True
        else:
            dart_type = TYPE_MAP.get(py_type, 'dynamic')
            
        # Gestion des Listes
        if py_type == 'array':
            items = field_info.get('items', {})
            if '$ref' in items:
                inner = items['$ref'].split('/')[-1].replace("Response", "").replace("Schema", "")
                dart_type = f"List<{inner}>"
                is_list_complex = True
            else:
                inner = TYPE_MAP.get(items.get('type', 'any'), 'dynamic')
                dart_type = f"List<{inner}>"

        # Gestion Nullable
        is_nullable = False
        if 'anyOf' in field_info:
            for t in field_info['anyOf']:
                if t.get('type') == 'null':
                    is_nullable = True
        
        # Variable Dart
        var_name = to_camel_case(field_name)
        final_type = f"{dart_type}{'?' if is_nullable else ''}"
        
        properties.append(f"  final {final_type} {var_name};")
        
        # --- FROM JSON ---
        json_access = f"json['{field_name}']"
        val_parse = json_access
        
        if 'DateTime' in dart_type:
            val_parse = f"{json_access} != null ? DateTime.tryParse({json_access}.toString()) : null"
            if not is_nullable: val_parse += " ?? DateTime.now()"
        elif 'double' in dart_type:
            val_parse = f"({json_access} as num?)?.toDouble()"
            if not is_nullable: val_parse += " ?? 0.0"
        elif is_list_complex:
            inner_type = dart_type.replace("List<", "").replace(">", "").replace("?", "")
            val_parse = f"({json_access} as List?)?.map((e) => {inner_type}.fromJson(e)).toList()"
            if not is_nullable: val_parse += " ?? []"
        elif is_complex:
            inner_type = dart_type.replace("?", "")
            val_parse = f"{json_access} != null ? {inner_type}.fromJson({json_access}) : null"
            
        elif not is_nullable:
            # Valeurs par défaut de sécurité
            if 'int' in dart_type: val_parse += " ?? 0"
            elif 'String' in dart_type: val_parse += " ?? ''"
            elif 'bool' in dart_type: val_parse += " ?? false"
            elif 'List' in dart_type: val_parse += " ?? []"
            elif 'Map' in dart_type: val_parse += " ?? {}"
            
        from_json_logic.append(f"      {var_name}: {val_parse},")
        
        # --- TO JSON ---
        val_export = var_name
        if 'DateTime' in dart_type:
            val_export = f"{var_name}?.toIso8601String()"
        elif is_list_complex:
            val_export = f"{var_name}?.map((e) => e.toJson()).toList()"
        elif is_complex:
            val_export = f"{var_name}?.toJson()"
            
        to_json_logic.append(f"      '{field_name}': {val_export},")

    # --- CODE FINAL ---
    return f"""// GÉNÉRÉ AUTOMATIQUEMENT - NE PAS MODIFIER
// Timestamp : {datetime.datetime.now().isoformat()}

class {dart_class_name} {{
{chr(10).join(properties)}

  {dart_class_name}({{
    {', '.join([f"required this.{to_camel_case(k)}" if 'null' not in v.get('type', '') and 'anyOf' not in v else f"this.{to_camel_case(k)}" for k,v in props.items()])}
  }});

  factory {dart_class_name}.fromJson(Map<String, dynamic> json) {{
    return {dart_class_name}(
{chr(10).join(from_json_logic)}
    );
  }}

  Map<String, dynamic> toJson() {{
    return {{
{chr(10).join(to_json_logic)}
    }};
  }}
}}
"""

# ==============================================================================
# 4. EXÉCUTION
# ==============================================================================

if __name__ == "__main__":
    if not FRONTEND_MODELS_DIR.exists():
        print(f"🛠️ Création du dossier cible : {FRONTEND_MODELS_DIR}")
        os.makedirs(FRONTEND_MODELS_DIR, exist_ok=True)
    
    print("\n🚀 Démarrage de la génération...")
    count = 0
    
    for model in MODELS_TO_GENERATE:
        try:
            dart_code = generate_dart_code(model)
            filename = get_dart_filename(model.__name__)
            file_path = FRONTEND_MODELS_DIR / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(dart_code)
                
            print(f"  ✨ {model.__name__: <25} -> {filename}")
            count += 1
        except Exception as e:
            print(f"  ❌ Erreur sur {model.__name__}: {e}")

    print(f"\n🎉 TERMINÉ : {count} fichiers générés.")
    print(f"👉 Emplacement : {FRONTEND_MODELS_DIR}")