import sys
import os
import json
import re
import datetime
from pathlib import Path

# ==============================================================================
# 1. SETUP
# ==============================================================================
print("🔍 Initialisation du scanner de projet...")
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = None
search_dir = SCRIPT_PATH.parent
for _ in range(5):
    if (search_dir / "backend").exists() and (search_dir / "frontend").exists():
        PROJECT_ROOT = search_dir
        break
    if search_dir.parent == search_dir: break
    search_dir = search_dir.parent

if PROJECT_ROOT is None:
    print("❌ ERREUR : Racine du projet introuvable.")
    sys.exit(1)

BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_MODELS_DIR = PROJECT_ROOT / "frontend" / "lib" / "models" / "generated"
sys.path.append(str(BACKEND_DIR))

# ==============================================================================
# 2. IMPORTATION
# ==============================================================================
try:
    from app.models.schemas import (
        UserResponse, Token, AthleteProfileResponse,
        CoachMemoryResponse, CoachEngramResponse,
        WorkoutSessionResponse, WorkoutSetResponse,
        AIWorkoutPlan, AIExercise, WeeklyPlanResponse, StrategyResponse, ProfileAuditResponse,
        FeedItemResponse, OneRepMaxResponse, ACWRResponse,
        # ✅ AJOUT DES SOUS-MODÈLES MANQUANTS
        BasicInfo, PhysicalMetrics, SportContext, TrainingPreferences
    )
    from app.models.enums import (
        MemoryType, ImpactLevel, MemoryStatus, FeedItemType, SportType, EquipmentType
    )
    print("✅ Modèles importés.")
except ImportError as e:
    print(f"❌ ERREUR IMPORT : {e}")
    sys.exit(1)

# Liste complète des classes à générer
MODELS = [
    UserResponse, Token, 
    AthleteProfileResponse, BasicInfo, PhysicalMetrics, SportContext, TrainingPreferences,
    CoachMemoryResponse, CoachEngramResponse,
    WorkoutSessionResponse, WorkoutSetResponse, 
    AIWorkoutPlan, AIExercise,
    WeeklyPlanResponse, StrategyResponse, ProfileAuditResponse, 
    FeedItemResponse, OneRepMaxResponse, ACWRResponse
]

ENUMS = [MemoryType, ImpactLevel, MemoryStatus, FeedItemType, SportType, EquipmentType]

# ==============================================================================
# 3. GENERATEUR DART INTELLIGENT
# ==============================================================================
TYPE_MAP = {
    'str': 'String', 'int': 'int', 'float': 'double', 'bool': 'bool', 
    'datetime': 'DateTime', 'date': 'DateTime', 'dict': 'Map<String, dynamic>', 
    'list': 'List', 'any': 'dynamic'
}

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def get_dart_filename(class_name):
    # Nettoyage du nom pour le fichier (UserResponse -> user.dart)
    clean = class_name.replace("Response", "").replace("Schema", "")
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', clean)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower() + ".dart"

def get_clean_classname(class_name):
    return class_name.replace("Response", "").replace("Schema", "")

def generate_dart_code(model, all_models_names, all_enums_names):
    raw_name = model.__name__
    cls_name = get_clean_classname(raw_name)
    
    try: schema = model.model_json_schema()
    except: schema = model.schema()
    
    props = schema.get('properties', {})
    fields = []
    ctor_params = []
    from_json = []
    to_json = []
    imports_set = set() # Pour stocker les fichiers à importer
    
    for fname, info in props.items():
        # --- 1. DÉTECTION DU TYPE ---
        py_type = info.get('type', 'any')
        dart_type = "dynamic"
        ref_obj = None
        
        # Extraction de la référence ($ref)
        if '$ref' in info: ref_obj = info['$ref'].split('/')[-1]
        elif 'allOf' in info and '$ref' in info['allOf'][0]: ref_obj = info['allOf'][0]['$ref'].split('/')[-1]
        elif 'anyOf' in info:
            for opt in info['anyOf']:
                if '$ref' in opt: ref_obj = opt['$ref'].split('/')[-1]
        
        is_complex = False
        is_enum = False
        is_list_complex = False
        
        if ref_obj:
            clean_ref = get_clean_classname(ref_obj)
            dart_type = clean_ref
            
            # Est-ce un Enum ou une autre Classe ?
            if ref_obj in all_enums_names or clean_ref in all_enums_names:
                is_enum = True
                imports_set.add("enums.dart")
            else:
                is_complex = True
                # ✅ Ajout de l'import automatique
                target_file = get_dart_filename(ref_obj)
                if target_file != get_dart_filename(raw_name): # Pas d'auto-import
                    imports_set.add(target_file)
        else:
            dart_type = TYPE_MAP.get(py_type, 'dynamic')
            
        # Gestion des Listes
        if py_type == 'array':
            items = info.get('items', {})
            inner_ref = None
            
            if '$ref' in items: inner_ref = items['$ref'].split('/')[-1]
            elif 'anyOf' in items: # Cas List[Union[...]]
                 for opt in items['anyOf']:
                    if '$ref' in opt: inner_ref = opt['$ref'].split('/')[-1]

            if inner_ref:
                inner_clean = get_clean_classname(inner_ref)
                dart_type = f"List<{inner_clean}>"
                
                if inner_ref in all_enums_names or inner_clean in all_enums_names:
                    # List<Enum> (Rare mais possible)
                    imports_set.add("enums.dart") 
                else:
                    is_list_complex = True
                    target_file = get_dart_filename(inner_ref)
                    imports_set.add(target_file)
            else:
                inner = TYPE_MAP.get(items.get('type', 'any'), 'dynamic')
                dart_type = f"List<{inner}>"

        # --- 2. GESTION NULLABILITÉ & REQUIRED ---
        is_nullable = False
        if 'anyOf' in info:
            for t in info['anyOf']:
                if t.get('type') == 'null': is_nullable = True
        
        # dynamic ne prend jamais de ?
        if dart_type == 'dynamic': is_nullable = False 
        
        var_name = to_camel_case(fname)
        final_type = f"{dart_type}{'?' if is_nullable else ''}"
        
        fields.append(f"  final {final_type} {var_name};")
        
        # Constructeur
        # Si non-nullable, c'est required. Sinon c'est optionnel.
        req = "required " if not is_nullable else ""
        ctor_params.append(f"{req}this.{var_name}")
        
        # --- 3. FROM JSON (Parsing) ---
        acc = f"json['{fname}']"
        val = acc
        
        if is_enum:
            # Enum: fallback safe
            safe_default = f"{dart_type}.values.first"
            if is_nullable:
                val = f"{acc} != null ? {dart_type}.fromJson({acc}) : null"
            else:
                val = f"{acc} != null ? {dart_type}.fromJson({acc}) : {safe_default}"
                
        elif is_complex:
            # Objet Complexe
            if is_nullable:
                val = f"{acc} != null ? {dart_type}.fromJson({acc}) : null"
            else:
                # Force non-null (au pire crash ou map vide, mais respecte le type)
                val = f"{dart_type}.fromJson({acc} ?? {{}})"
                
        elif is_list_complex:
            # Liste d'Objets
            inner = dart_type.replace("List<", "").replace(">", "")
            val = f"({acc} as List?)?.map((e) => {inner}.fromJson(e)).toList()"
            if not is_nullable: val += " ?? []"
            
        elif 'DateTime' in dart_type:
            val = f"{acc} != null ? DateTime.tryParse({acc}.toString()) : null"
            if not is_nullable: val += " ?? DateTime.now()"
            
        elif 'double' in dart_type:
            val = f"({acc} as num?)?.toDouble()"
            if not is_nullable: val += " ?? 0.0"
            
        elif not is_nullable:
            # Primitifs non-nullables : valeurs par défaut
            if 'int' in dart_type: val += " ?? 0"
            elif 'String' in dart_type: val += " ?? ''"
            elif 'bool' in dart_type: val += " ?? false"
            elif 'List' in dart_type: val += " ?? []"
            elif 'Map' in dart_type: val += " ?? {}"
            
        from_json.append(f"      {var_name}: {val},")
        
        # --- 4. TO JSON (Export) ---
        exp = var_name
        # Opérateur null-aware si nullable
        op = "?." if is_nullable else "."
        
        if 'DateTime' in dart_type: exp = f"{var_name}{op}toIso8601String()"
        elif is_enum: exp = f"{var_name}{op}toJson()"
        elif is_list_complex: exp = f"{var_name}{op}map((e) => e.toJson()).toList()"
        elif is_complex: exp = f"{var_name}{op}toJson()"
            
        to_json.append(f"      '{fname}': {exp},")

    # Génération des imports
    imports_code = "\n".join([f"import '{f}';" for f in sorted(imports_set)])
    
    return f"""// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : {datetime.datetime.now().isoformat()}

{imports_code}

class {cls_name} {{
{chr(10).join(fields)}

  {cls_name}({{
    {', '.join(ctor_params)}
  }});

  factory {cls_name}.fromJson(Map<String, dynamic> json) {{
    return {cls_name}(
{chr(10).join(from_json)}
    );
  }}

  Map<String, dynamic> toJson() {{
    return {{
{chr(10).join(to_json)}
    }};
  }}
}}
"""

def generate_enums(enums_list, path):
    content = f"// GÉNÉRÉ AUTOMATIQUEMENT\n// Timestamp : {datetime.datetime.now().isoformat()}\n\n"
    for e in enums_list:
        name = e.__name__
        vals = [v.name for v in e]
        default = vals[-1] if "OTHER" in vals else vals[0]
        
        content += f"enum {name} {{\n  " + ",\n  ".join(vals) + ";\n\n"
        content += f"  String toJson() => name;\n"
        content += f"  static {name} fromJson(dynamic json) {{\n"
        content += f"    return {name}.values.firstWhere((e) => e.name == json.toString(), orElse: () => {default});\n"
        content += "  }\n}\n\n"
        
    with open(path, "w", encoding="utf-8") as f: f.write(content)

# ==============================================================================
# 4. EXECUTION
# ==============================================================================
if __name__ == "__main__":
    if not FRONTEND_MODELS_DIR.exists(): os.makedirs(FRONTEND_MODELS_DIR, exist_ok=True)
    
    # Prépare les listes de noms pour la détection
    model_names = [m.__name__ for m in MODELS]
    clean_model_names = [get_clean_classname(n) for n in model_names]
    enum_names = [e.__name__ for e in ENUMS]
    
    print("\n🚀 Génération des Modèles...")
    for m in MODELS:
        code = generate_dart_code(m, model_names + clean_model_names, enum_names)
        path = FRONTEND_MODELS_DIR / get_dart_filename(m.__name__)
        with open(path, "w") as f: f.write(code)
        print(f"  ✨ {get_clean_classname(m.__name__)}")

    print("\n🚀 Génération des Enums...")
    generate_enums(ENUMS, FRONTEND_MODELS_DIR / "enums.dart")
    print("  ✨ enums.dart")
    
    print("\n✅ Terminé.")