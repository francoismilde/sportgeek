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
# 2. IMPORTATION DES MODÈLES ET ENUMS
# ==============================================================================
try:
    # --- SCHEMAS (Classes) ---
    from app.models.schemas import (
        UserResponse, Token,
        AthleteProfileResponse,
        CoachMemoryResponse, CoachEngramResponse,
        WorkoutSessionResponse, WorkoutSetResponse,
        AIWorkoutPlan, AIExercise, WeeklyPlanResponse, StrategyResponse, ProfileAuditResponse,
        FeedItemResponse,
        OneRepMaxResponse, ACWRResponse
    )
    
    # --- ENUMS (Types) ---
    # Assure-toi que ces Enums existent bien dans app.models.enums
    from app.models.enums import (
        MemoryType, 
        ImpactLevel, 
        MemoryStatus, 
        FeedItemType, 
        # Ajoute ici d'autres enums si nécessaire (ex: SportType, etc.)
    )
    
    print("✅ Modèles et Enums importés avec succès.")
except ImportError as e:
    print(f"\n❌ ERREUR D'IMPORT PYTHON : {e}")
    print("   Vérifiez que votre environnement virtuel est activé.")
    print("   (source venv/bin/activate)")
    sys.exit(1)

# Liste des modèles (Classes) à convertir en fichiers individuels
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

# Liste des Enums à regrouper dans enums.dart
ENUMS_TO_GENERATE = [
    MemoryType,
    ImpactLevel,
    MemoryStatus,
    FeedItemType
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
    """Nettoie le nom de la classe pour le fichier"""
    clean_name = class_name.replace("Response", "").replace("Schema", "")
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', clean_name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower() + ".dart"

def generate_dart_code(pydantic_model):
    """Génère le code source Dart pour un modèle Pydantic (Classe)"""
    
    raw_name = pydantic_model.__name__
    dart_class_name = raw_name.replace("Response", "").replace("Schema", "")
    
    properties = []
    from_json_logic = []
    to_json_logic = []
    
    try:
        schema = pydantic_model.model_json_schema() # Pydantic V2
    except AttributeError:
        schema = pydantic_model.schema() # Pydantic V1
        
    props = schema.get('properties', {})
    
    # Imports potentiels (si besoin d'enums, etc.)
    # Pour simplifier, on suppose que les classes complexes sont dans le même dossier
    # Mais pour les Enums, on doit savoir s'ils sont utilisés.
    
    for field_name, field_info in props.items():
        py_type = field_info.get('type', 'any')
        dart_type = "dynamic"
        
        # Gestion des références ($ref)
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
        is_enum = False
        
        if ref_obj:
            # Vérifier si c'est un Enum connu
            clean_ref = ref_obj.replace("Response", "").replace("Schema", "")
            if clean_ref in [e.__name__ for e in ENUMS_TO_GENERATE]:
                dart_type = clean_ref # C'est un Enum !
                is_enum = True
            else:
                dart_type = clean_ref # C'est une autre Classe
                is_complex = True
        else:
            dart_type = TYPE_MAP.get(py_type, 'dynamic')
            
        # Gestion des Listes
        if py_type == 'array':
            items = field_info.get('items', {})
            if '$ref' in items:
                inner = items['$ref'].split('/')[-1].replace("Response", "").replace("Schema", "")
                dart_type = f"List<{inner}>"
                is_list_complex = True # Note: pourrait être une liste d'Enums, à affiner si besoin
            else:
                inner = TYPE_MAP.get(items.get('type', 'any'), 'dynamic')
                dart_type = f"List<{inner}>"

        is_nullable = False
        if 'anyOf' in field_info:
            for t in field_info['anyOf']:
                if t.get('type') == 'null':
                    is_nullable = True
        
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
        elif is_enum:
            # Parsing d'Enum
            val_parse = f"{json_access} != null ? {dart_type}.fromJson({json_access}) : null"
            if not is_nullable: 
                # Valeur par défaut safe (la dernière ou la première)
                val_parse += f" ?? {dart_type}.values.first"
        elif is_list_complex:
            inner_type = dart_type.replace("List<", "").replace(">", "").replace("?", "")
            val_parse = f"({json_access} as List?)?.map((e) => {inner_type}.fromJson(e)).toList()"
            if not is_nullable: val_parse += " ?? []"
        elif is_complex:
            inner_type = dart_type.replace("?", "")
            val_parse = f"{json_access} != null ? {inner_type}.fromJson({json_access}) : null"
            
        elif not is_nullable:
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
        elif is_enum:
            val_export = f"{var_name}?.toJson()"
        elif is_list_complex:
            val_export = f"{var_name}?.map((e) => e.toJson()).toList()"
        elif is_complex:
            val_export = f"{var_name}?.toJson()"
            
        to_json_logic.append(f"      '{field_name}': {val_export},")

    # Si des enums sont utilisés, on doit importer le fichier d'enums
    # Pour faire simple, on l'ajoute toujours
    import_enums = "import 'enums.dart';" 

    return f"""// GÉNÉRÉ AUTOMATIQUEMENT - NE PAS MODIFIER
// Timestamp : {datetime.datetime.now().isoformat()}

{import_enums}

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

def generate_enums_file(enums_list, output_path):
    """Génère le fichier unique enums.dart pour tous les Enums"""
    
    content = f"// GÉNÉRÉ AUTOMATIQUEMENT - NE PAS MODIFIER\n"
    content += f"// Timestamp : {datetime.datetime.now().isoformat()}\n\n"
    content += "// Ce fichier regroupe tous les Enums utilisés par les modèles\n\n"
    
    for enum_class in enums_list:
        class_name = enum_class.__name__
        values = [e.name for e in enum_class]
        
        # Valeur par défaut (Fallback)
        default_val = values[-1] if "OTHER" in values else values[0]
        
        content += f"enum {class_name} {{\n"
        content += "  " + ",\n  ".join(values) + ";\n\n"
        
        content += "  String toJson() => name;\n\n"
        
        content += f"  static {class_name} fromJson(dynamic json) {{\n"
        content += f"    if (json == null) return {default_val};\n"
        content += f"    return {class_name}.values.firstWhere(\n"
        content += f"      (e) => e.name == json.toString(),\n"
        content += f"      orElse: () => {default_val},\n"
        content += "    );\n"
        content += "  }\n"
        content += "}\n\n"
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✨ ENUMS GÉNÉRÉS : {output_path.name}")

# ==============================================================================
# 4. EXÉCUTION
# ==============================================================================

if __name__ == "__main__":
    if not FRONTEND_MODELS_DIR.exists():
        print(f"🛠️ Création du dossier cible : {FRONTEND_MODELS_DIR}")
        os.makedirs(FRONTEND_MODELS_DIR, exist_ok=True)
    
    print("\n🚀 Démarrage de la génération...")
    count = 0
    
    # 1. Génération des Classes
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